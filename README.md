# The code and data for the paper "A More Fine-Grained Aspect-Sentiment-Opinion Triplet Extraction Task" [paper](https://arxiv.org/pdf/2103.15255.pdf)

# ASOTE
Aspect-Sentiment-Opinion Triplet Extraction (ASOTE) extracts aspect term, sentiment and opinion term triplets from sentences. In the triplet extracted by ASOTE the sentiment is the sentiment of the aspect term and opinion term pair. For example, given the sentence, "The atmosphere is attractive , but a little uncomfortable.", ASOTE extracts two triplets, ("atmosphere", positive, "attractive") and ("atmosphere", negative, "uncomfortable").

# Differences between ASOTE and ASTE
Aspect Sentiment Triplet Extraction (ASTE) ([Knowing What, How and Why: A Near Complete Solution for Aspect-based Sentiment Analysis](https://arxiv.org/abs/1911.01616)) also extracts triplets from sentences. Each triplet extracted by ASTE contains an aspect term, <u>the sentiment that the sentence expresses toward the aspect term</u>, and one opinion term associated with the aspect.

![](figures/asote_vs_aste.png)
In the third sentence, the negative sentiment toward the aspect term “food” isexpressed without an annotatable opinion.

A few models have been proposed for the ASTE task. We have evaluated their performances on the ASOTE task.
- [Position-Aware Tagging for Aspect Sentiment Triplet Extraction](https://arxiv.org/pdf/2010.02609.pdf). Lu Xu, Hao Li, Wei Lu, Lidong Bing. In EMNLP, 2020. [code & data](https://github.com/xuuuluuu/Position-Aware-Tagging-for-ASTE)
- [Grid Tagging Scheme for Aspect-oriented Fine-grained Opinion Extraction](https://arxiv.org/pdf/2010.04640.pdf). Zhen Wu, Chengcan Ying, Fei Zhao, Zhifang Fan, Xinyu Dai, Rui Xia. In Findings of EMNLP, 2020. [code & data](https://github.com/NJUNLP/GTS)
- [A Multi-task Learning Framework for Opinion Triplet Extraction](https://arxiv.org/abs/2010.01512). Chen Zhang, Qiuchi Li, Dawei Song, Benyou Wang. In Findings of EMNLP, 2020. [code & data](https://github.com/GeneZC/OTE-MTL)

# Data
We build four datasets for the ASOTE task: [14res](ASOTE-data/absa/ASOTE/rest14), [14lap](ASOTE-data/absa/ASOTE/lapt14), [15res](ASOTE-data/absa/ASOTE/rest15), [16res](ASOTE-data/absa/ASOTE/rest16).

# Requirements
- Python 3.6.8
- torch==1.2.0
- pytorch-transformers==1.1.0
- allennlp==0.9.0

# Instructions:
1. Before excuting the following commands, replace glove.840B.300d.txt(http://nlp.stanford.edu/data/wordvecs/glove.840B.300d.zip), bert-base-uncased.tar.gz(https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased.tar.gz) and vocab.txt(https://s3.amazonaws.com/models.huggingface.co/bert/bert-base-uncased-vocab.txt) with the corresponding absolute paths in your computer. 
2. We only provide the 14res dataset for review.

# ATE
scripts/ate.sh

# TOWE
scripts/towe.sh

# TOWE inference
scripts/towe.predic.sh

# AOSC
scripts/tosc.sh

# U-ASO
scripts/towe_tosc_jointly.sh

# U-ASO inference
scripts/towe_tosc_jointly.predict.sh

# MIL-ASO
scripts/mil_aso.sh

# MIL-ASO inference
scripts/mil_aso.predict.sh

# evaluate
scripts/evaluate.sh
