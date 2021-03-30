# -*- coding: utf-8 -*-


import argparse
import sys
import random
import copy
from typing import List
import json
from collections import defaultdict
import os

import torch
import numpy

from nlp_tasks.absa.utils import argument_utils
from nlp_tasks.absa.mining_opinions.data_adapter import data_object
from nlp_tasks.utils import file_utils
from nlp_tasks.common import common_path

parser = argparse.ArgumentParser()
parser.add_argument('--current_dataset', help='dataset name', default='ASOTEDataRest14', type=str)
parser.add_argument('--ate_result_filepath_template', help='ate result filepath',
                    default=os.path.join(common_path.project_dir, 'ASOTE-data', 'absa', 'ASOTE-prediction-result', 'ATE', 'result_of_predicting_test.txt'), type=str)
parser.add_argument('--towe_result_filepath_template', help='towe result filepath',
                    default=os.path.join(common_path.project_dir, 'ASOTE-data', 'absa', 'ASOTE-prediction-result', 'TOWE', 'result_of_predicting_test.txt'), type=str)
parser.add_argument('--tosc_result_filepath_template', help='tosc result filepath',
                    default=os.path.join(common_path.project_dir, 'ASOTE-data', 'absa', 'ASOTE-prediction-result', 'TOSC', 'result_of_predicting_test.txt'), type=str)
parser.add_argument('--debug', help='debug', default=False, type=argument_utils.my_bool)
args = parser.parse_args()

configuration = args.__dict__

dataset_name = configuration['current_dataset']
dataset = data_object.get_dataset_class_by_name(dataset_name)()
train_dev_test_data = dataset.get_data_type_and_data_dict()


def generate_line_dicts(filepath: str):
    """

    :param filepath:
    :return:
    """
    lines = file_utils.read_all_lines(filepath)
    for line in lines:
        line_dict = json.loads(line)
        yield line_dict


def aspect_term_str_to_dict(aspect_term_str: str):
    """

    :param aspect_term_str:
    :return:
    """
    parts = aspect_term_str.split('-')
    aspect_term_text = '-'.join(parts[:-2])
    start = int(parts[-2])
    end = int(parts[-1])
    result = {'start': start, 'end': end, 'term': aspect_term_text}
    return result


def aspect_term_dict_to_str(aspect_term_dict: dict):
    """

    :param aspect_term_dict:
    :return:
    """
    result = '%s-%d-%d' % (aspect_term_dict['term'], aspect_term_dict['start'], aspect_term_dict['end'])
    return result


def read_ate_result(filepath):
    """

    :param filepath:
    :return:
    """
    result = {}
    line_dicts = generate_line_dicts(filepath)
    for line_dict in line_dicts:
        sentence = line_dict['text']
        aspect_terms = line_dict['pred']
        result[sentence] = aspect_terms
    return result


def read_tosc_result(filepath):
    """

    :param filepath:
    :return:
    """
    result = {}
    line_dicts = generate_line_dicts(filepath)
    for line_dict in line_dicts:
        sentence = line_dict['text']
        if sentence not in result:
            result[sentence] = []
        aspect_term = aspect_term_dict_to_str(line_dict['opinion']['aspect_term'])
        opinion_term = aspect_term_dict_to_str(line_dict['opinion']['opinion_term'])
        polarity = line_dict['sentiment_pred']
        result[sentence].append({'aspect_term': aspect_term, 'opinion_term': opinion_term, 'polarity': polarity})
    return result


def read_towe_result(filepath):
    """

    :param filepath:
    :return:
    """
    result = defaultdict(list)
    line_dicts = generate_line_dicts(filepath)
    for line_dict in line_dicts:
        sentence = line_dict['text']
        aspect_term = aspect_term_str_to_dict(line_dict['aspect_terms'][0])
        opinion_terms = [aspect_term_str_to_dict(e) for e in line_dict['pred']]
        result[sentence].append({'aspect_term': aspect_term, 'opinions': opinion_terms})
    return result


def merge_results_of_subtasks(ate_result, tosc_result, towe_result):
    """

    :param ate_result:
    :param tosc_result:
    :param towe_result:
    :return:
    """
    result = {}
    for sentence in ate_result.keys():
        if sentence not in result:
            result[sentence] = []

        aspect_terms = ate_result[sentence]

        opinions = towe_result[sentence]
        aspect_and_opinions = {}
        for opinion in opinions:
            aspect_term = aspect_term_dict_to_str(opinion['aspect_term'])
            opinion_terms = [aspect_term_dict_to_str(e) for e in opinion['opinions']]
            aspect_and_opinions[aspect_term] = opinion_terms

        aspect_opinion_and_sentiment = {}
        if sentence in tosc_result:
            polarities = tosc_result[sentence]
            for polarity in polarities:
                aspect_opinion_and_sentiment['%s_%s' % (polarity['aspect_term'], polarity['opinion_term'])] = \
                    polarity['polarity']

        for aspect in aspect_terms:
            if aspect not in aspect_and_opinions or len(aspect_and_opinions[aspect]) == 0:
                continue
            opinions = aspect_and_opinions[aspect]
            for opinion in opinions:
                key = '%s_%s' % (aspect, opinion)
                sentiment = '-'
                if key in aspect_opinion_and_sentiment:
                    sentiment = aspect_opinion_and_sentiment[key]
                result[sentence].append('%s_%s_%s' % (aspect, sentiment, opinion))
    return result


def generate_subtasks_true(test_data):
    """

    :param test_data:
    :return:
    """
    sentence_and_triplets = {}
    for sample in test_data:
        original_line_data = sample.metadata['original_line_data']
        sentence = original_line_data['sentence']
        if sentence not in sentence_and_triplets:
            sentence_and_triplets[sentence] = []

        opinions = original_line_data['opinions']
        for opinion in opinions:
            if 'polarity' not in opinion:
                continue
            aspect_term = opinion['aspect_term']
            opinion_term = opinion['opinion_term']
            triplet_str = '%s_%s_%s' % (aspect_term_dict_to_str(aspect_term), opinion['polarity'],
                                        aspect_term_dict_to_str(opinion_term))
            sentence_and_triplets[sentence].append(triplet_str)
    return sentence_and_triplets


def triplets_of_sentence(results_of_subtasks_of_sentence):
    """

    :param results_of_subtasks_of_sentence:
    :return:
    """
    aspect_terms = results_of_subtasks_of_sentence['aspect_terms']
    polarities = results_of_subtasks_of_sentence['polarities']
    opinions = results_of_subtasks_of_sentence['opinions']

    aspect_term_strs = [aspect_term_dict_to_str(e) for e in aspect_terms]

    aspect_term_str_and_sentiment = {}
    for e in polarities:
        aspect_term_str_and_sentiment[aspect_term_dict_to_str(e['aspect_term'])] = e['polarity']

    aspect_term_str_and_opinions = {}
    for e in opinions:
        aspect_term_str = aspect_term_dict_to_str(e['aspect_term'])
        opinions_of_this_aspect: List = e['opinions']
        if len(opinions_of_this_aspect) == 0:
            continue
        opinions_of_this_aspect.sort(key=lambda x: x['start'])
        opinion_strs_of_this_aspect = [aspect_term_dict_to_str(e) for e in opinions_of_this_aspect]
        aspect_term_str_and_opinions[aspect_term_str] = '_'.join(opinion_strs_of_this_aspect)
    results = set()
    for aspect_term_str in aspect_term_strs:
        sentiment = '-'
        # 模型会对每个召回的aspect term预测情感，但是为了便于评估，我们只会预测ground truth aspect term的情感，所以用-指示错误的情感
        # (假设，假设不存在的aspect term的情感一定是错的)
        if aspect_term_str in aspect_term_str_and_sentiment:
            sentiment = aspect_term_str_and_sentiment[aspect_term_str]

        if aspect_term_str in aspect_term_str_and_opinions:
            multiple_opinions = aspect_term_str_and_opinions[aspect_term_str]
            results.add('%s__%s__%s' % (aspect_term_str, sentiment, multiple_opinions))
    return results


def aspect_terms_of_sentence(results_of_subtasks_of_sentence):
    """

    :param results_of_subtasks_of_sentence:
    :return:
    """
    aspect_terms = results_of_subtasks_of_sentence['aspect_terms']

    result = set([aspect_term_dict_to_str(e) for e in aspect_terms])
    return result


def aspect_sentiment_of_sentence(results_of_subtasks_of_sentence):
    """

    :param results_of_subtasks_of_sentence:
    :return:
    """
    polarities = results_of_subtasks_of_sentence['polarities']

    result = set()
    for e in polarities:
        result.add('%s__%s' % (aspect_term_dict_to_str(e['aspect_term']), e['polarity']))
    return result


def aspect_opinions_of_sentence(results_of_subtasks_of_sentence):
    """

    :param results_of_subtasks_of_sentence:
    :return:
    """
    opinions = results_of_subtasks_of_sentence['opinions']

    result = set()
    for e in opinions:
        aspect_term_str = aspect_term_dict_to_str(e['aspect_term'])
        opinions_of_this_aspect: List = e['opinions']
        if len(opinions_of_this_aspect) == 0:
            continue
        opinions_of_this_aspect.sort(key=lambda x: x['start'])
        opinion_strs_of_this_aspect = [aspect_term_dict_to_str(e) for e in opinions_of_this_aspect]
        for opinion_str_of_this_aspect in opinion_strs_of_this_aspect:
            result.add('%s__%s' % (aspect_term_str, opinion_str_of_this_aspect))
    return result


def get_metrics(true_num, pred_num, tp):
    """

    :param true_num:
    :param pred_num:
    :param tp:
    :return:
    """
    precision = tp / pred_num
    recall = tp / true_num
    f1 = 2 * precision * recall / (precision + recall)
    return {'precision': '%.3f' % (precision * 100), 'recall': '%.3f' % (recall * 100), 'f1': '%.3f' % (f1 * 100)}


def evaluate_asote(sentences_true, sentences_pred):
    """

    :param sentences_true:
    :param sentences_pred:
    :return:
    """
    true_triplet_num = 0
    pred_triplet_num = 0
    tp = 0
    for sentence in sentences_true.keys():
        triplets_true = sentences_true[sentence]
        triplets_pred = sentences_pred[sentence]

        true_triplet_num += len(triplets_true)
        pred_triplet_num += len(triplets_pred)

        for e in triplets_true:
            if e in triplets_pred:
                tp += 1
    result = get_metrics(true_triplet_num, pred_triplet_num, tp)
    return result


def evaluate_ate(sentences_true, sentences_pred):
    """

    :param sentences_true:
    :param sentences_pred:
    :return:
    """
    true_aspect_term_num = 0
    pred_aspect_term_num = 0
    tp = 0
    for sentence in sentences_true.keys():
        sentence_true = sentences_true[sentence]
        sentence_pred = sentences_pred[sentence]

        aspect_terms_true = aspect_terms_of_sentence(sentence_true)
        aspect_terms_pred = aspect_terms_of_sentence(sentence_pred)

        true_aspect_term_num += len(aspect_terms_true)
        pred_aspect_term_num += len(aspect_terms_pred)

        for e in aspect_terms_true:
            if e in aspect_terms_pred:
                tp += 1
    result = get_metrics(true_aspect_term_num, pred_aspect_term_num, tp)
    return result


def evaluate_atsa(sentences_true, sentences_pred):
    """

    :param sentences_true:
    :param sentences_pred:
    :return:
    """
    total_num = 0
    correct_num = 0
    for sentence in sentences_true.keys():
        sentence_true = sentences_true[sentence]
        sentence_pred = sentences_pred[sentence]

        aspect_sentiment_true = aspect_sentiment_of_sentence(sentence_true)
        aspect_sentiment_pred = aspect_sentiment_of_sentence(sentence_pred)

        total_num += len(aspect_sentiment_true)

        for e in aspect_sentiment_true:
            if e in aspect_sentiment_pred:
                correct_num += 1
    result = {'accuracy': '%.3f' % (correct_num / total_num * 100)}
    return result


def evaluate_towe(sentences_true, sentences_pred):
    """

    :param sentences_true:
    :param sentences_pred:
    :return:
    """
    true_aspect_opinion_num = 0
    pred_aspect_opinion_num = 0
    tp = 0
    for sentence in sentences_true.keys():
        sentence_true = sentences_true[sentence]
        sentence_pred = sentences_pred[sentence]

        aspect_opinions_true = aspect_opinions_of_sentence(sentence_true)
        aspect_opinions_pred = aspect_opinions_of_sentence(sentence_pred)

        true_aspect_opinion_num += len(aspect_opinions_true)
        pred_aspect_opinion_num += len(aspect_opinions_pred)

        for e in aspect_opinions_true:
            if e in aspect_opinions_pred:
                tp += 1
    result = get_metrics(true_aspect_opinion_num, pred_aspect_opinion_num, tp)
    return result


def print_precision_recall_f1(metrics_of_multi_runs, description: str = ''):
    """

    :param metrics_of_multi_runs:
    :param description:
    :return:
    """
    print(description)
    precisions = []
    recalls = []
    f1s = []
    for e in metrics_of_multi_runs:
        precisions.append(e['precision'])
        recalls.append(e['recall'])
        f1s.append(e['f1'])
    print('precision: %s' % ','.join(precisions))
    print('recall: %s' % ','.join(recalls))
    print('f1: %s' % ','.join(f1s))
    print('%s\t%s\t%s' % (','.join(precisions), ','.join(recalls), ','.join(f1s)))


def print_acc(metrics_of_multi_runs, description: str = ''):
    """

    :param metrics_of_multi_runs:
    :param description:
    :return:
    """
    print(description)
    print('acc: %s' % ','.join([e['accuracy'] for e in metrics_of_multi_runs]))


test_data = train_dev_test_data['test']
triplets_true = generate_subtasks_true(test_data)

ate_result_filepath_template = configuration['ate_result_filepath_template']
towe_result_filepath_template = configuration['towe_result_filepath_template']
tosc_result_filepath_template = configuration['tosc_result_filepath_template']

run_num = 5
asote_metrics_of_multi_runs = []
for i in range(run_num):
    if args.debug:
        ate_result_filepath = ate_result_filepath_template
        towe_result_filepath = towe_result_filepath_template
        tosc_result_filepath = tosc_result_filepath_template
    else:
        ate_result_filepath = ate_result_filepath_template % i
        towe_result_filepath = towe_result_filepath_template % i
        tosc_result_filepath = tosc_result_filepath_template % i
    if not os.path.exists(ate_result_filepath):
        print('not exist: %s' % ate_result_filepath)
        continue

    if not os.path.exists(towe_result_filepath):
        print('not exist: %s' % towe_result_filepath)
        continue

    if not os.path.exists(tosc_result_filepath):
        print('not exist: %s' % tosc_result_filepath)
        continue

    ate_pred = read_ate_result(ate_result_filepath)
    towe_pred = read_towe_result(towe_result_filepath)
    tosc_pred = read_tosc_result(tosc_result_filepath)
    triplets_pred = merge_results_of_subtasks(ate_pred, tosc_pred, towe_pred)

    asote_metrics_of_multi_runs.append(evaluate_asote(triplets_true, triplets_pred))


print_precision_recall_f1(asote_metrics_of_multi_runs, 'asote_metrics_of_multi_runs')