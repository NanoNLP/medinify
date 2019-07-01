
# Python Libraries
import pickle
import argparse
import json
import datetime
from time import time
import warnings

# Preprocessings
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from nltk import RegexpTokenizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

# Classification
from sklearn import svm

# Evaluation
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import confusion_matrix
# from sklearn.model_selection import train_test_split, GridSearchCV, RandomizedSearchCV

# NN (Currently Unused)
from keras.models import Sequential
from keras.models import model_from_json
from keras.layers import Dense, Dropout


class ReviewClassifier:
    """
    This class is used for the training and evaluation of supervised machine learning classifiers,
    currently including Multinomial Naive Bayes, Random Forest, and Support Vector Machine (all
    implemented using the SciKit Learn library) for the sentiment analysis of online drug reviews

    Attributes:

        classifier_type: str
            acronym for the type of machine learning algorithm used
            ('nb' - Multinomial Naive Bayes, 'rf' - Random Forest, 'svm' - Support Vector Machine)

        model: MultinomialNaiveBayes, RandomForestClassifier, or LinearSVC (depending on classifier type)
            an instance's trained or training classification model

        negative_threshold: float
            star-rating cutoff at with anything <= is labelled negative (default 2.0)

        positive_threshold: float
            star-rating cutoff at with anything >= is labelled positive (default 4.0)

        vectorizer: CountVectorizer or TfidfVectorizer
            object for turning dictionary of tokens into numerical representation (vector)
    """

    classifier_type = None
    model = None
    negative_threshold = 2.0
    positive_threshold = 4.0
    vectorizer = None

    def __init__(self, classifier_type=None, negative_threshold=None, positive_threshold=None, use_tfidf=False):
        """
        Initialize an instance of ReviewClassifier for the processing of review data into numerical
        representations, training machine-learning classifiers, and evaluating these classifiers' effectiveness
        :param classifier_type: SciKit Learn supervised machine-learning classifier ('nb', 'svm', or 'rf')
        :param negative_threshold: star-rating cutoff at with anything <= is labelled negative (default 2.0)
        :param positive_threshold: star-rating cutoff at with anything >= is labelled positive (default 4.0)
        :param use_tfidf: whether or not to set vectorizer to TF-IDF vectorizer (vectorizer
            is default CountVectorizer)
        """

        self.classifier_type = classifier_type
        if not use_tfidf:
            self.vectorizer = CountVectorizer()
        else:
            self.vectorizer = TfidfVectorizer()

        if negative_threshold:
            self.negative_threshold = negative_threshold
        if positive_threshold:
            self.positive_threshold = positive_threshold

    def preprocess(self, reviews_filename, num=2, remove_stop_words=True):
        """
        Transforms reviews (comments and ratings) into numerical representations (vectors)
        Comments are vectorized into bag-of-words representation
        Ratings are transformed into 0's (negative) and 1's (positive)
        Neutral reviews are discarded

        :param reviews_filename: CSV file with comments and ratings
        :param remove_stop_words: Whether or not to remove stop words
        :return:
        data: list of sparse matrices
            vectorized comments
        target: list of integers
            vectorized ratings
        """

        stop_words = set(stopwords.words('english'))
        tokenizer = RegexpTokenizer(r'\w+')
        df = pd.read_csv(reviews_filename)

        reviews, target = [], []
        num_pos, num_neg, num_neut = 0, 0, 0
        if num == 3:
            for review in df.values.tolist():
                #print('---')
                #print(review[1])
                if type(review[0]) == float:
                    continue
                if self.negative_threshold < review[1] < self.positive_threshold:
                    num_neut += 1
                    rating = 1
                elif review[1] <= self.negative_threshold:
                    num_neg += 1
                    rating = 0
                else:
                    num_pos += 1
                    rating = 2
                #print(rating)
                #print('---')
                target.append(rating)
                if remove_stop_words:
                    reviews.append(' '.join(word.lower() for word in tokenizer.tokenize(review[0])
                                            if word not in stop_words))
                else:
                    reviews.append(' '.join(word.lower() for word in tokenizer.tokenize(review[0])))
        elif num == 2:
            for review in df.values.tolist():
                # print(review[1])
                if type(review[0]) == float:
                    continue
                if self.negative_threshold < review[1] < self.positive_threshold:
                    num_neut += 1
                    continue
                elif review[1] <= self.negative_threshold:
                    num_neg += 1
                    rating = 0
                else:
                    num_pos += 1
                    rating = 1
                target.append(rating)
                if remove_stop_words:
                    reviews.append(' '.join(word.lower() for word in tokenizer.tokenize(review[0])
                                            if word not in stop_words))
                else:
                    reviews.append(' '.join(word.lower() for word in tokenizer.tokenize(review[0])))
        elif num == 5:
            onecount = 0
            twocount = 0
            redcount = 0
            bluecount = 0
            fivecount = 0
            for review in df.values.tolist():
                if type(review[0]) == float:
                    continue
                if review[1] == 1.0:
                    num_neg += 1
                    rating = 1
                    onecount += 1
                elif review[1] == 2.0:
                    num_neg += 1
                    rating = 2
                    twocount += 1
                elif review[1] == 3.0:
                    num_neut += 1
                    rating = 3
                    redcount += 1
                elif review[1] == 4.0:
                    num_pos += 1
                    rating = 4
                    bluecount += 1
                else:
                    num_pos += 1
                    rating = 5
                    fivecount += 1
                target.append(rating)
                if remove_stop_words:
                    reviews.append(' '.join(word.lower() for word in tokenizer.tokenize(review[0])
                                            if word not in stop_words))
                else:
                    reviews.append(' '.join(word.lower() for word in tokenizer.tokenize(review[0])))
            # print(onecount)
            # print(twocount)
            # print(redcount)
            # print(bluecount)
            # print(fivecount)
            # print('___')
        self.vectorizer.fit(reviews)
        data = np.array([self.vectorizer.transform([comment]).toarray() for comment in reviews]).squeeze(1)
        info = {'positive': num_pos, 'negative': num_neg, 'neutral': num_neut}

        return data, target, info

    def generate_model(self):
        """
        Creates model based on classifier type
        :return model: untrained machine learning classifier
        """

        model = None

        if self.classifier_type == 'nb':
            model = MultinomialNB(alpha=1, fit_prior=True)
        elif self.classifier_type == 'rf':
            model = RandomForestClassifier(n_estimators=100)
        elif self.classifier_type == 'svm':
            model = svm.LinearSVC(max_iter=10000)

        return model

    def fit(self, data, target):
        """
        Fits model to data and targets
        :param data: list of vectorized comments
        :param target: assosiated ratings (0's and 1's)
        :return model: trained machine learning classifier
        """

        model = self.generate_model()
        model.fit(data, target)
        self.model = model
        return model


    def evaluate_accuracy(self, data, target, num, model=None, verbose=False):
        """Evaluate accuracy of current model on new data

        Args:
            data: vectorized comments for feed into model
            target: actual ratings assosiated with data
            model: trained model to evaluate (if none, the class attribute 'model' will be evaluated)
            verbose: Whether or not to print formatted results to console
        """

        if model:
            preds = model.predict(data)
            # print(list(preds))
        else:
            preds = self.model.predict(data)
            # print(list(preds))
        if num == 2:
            accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2 = metrics(target, preds)
        if num == 3:
            accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2, precision3, recall3, f1_3 = metrics(target, preds, num=3)
        if num == 5:
            accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2, precision3, recall3, f1_3, precision4, recall4, f1_4, precision5, recall5, f1_5 = metrics(target, preds, num=5)
        if verbose and num == 2:
            print('Evaluation Metrics:')
            print('Accuracy: {}%'.format(accuracy * 100))
            print('Positive Precision: {}%'.format(precision1 * 100))
            print('Positive Recall: {}%'.format(recall1 * 100))
            print('Positive F1-Score: {}%'.format(f1_1 * 100))
            print('Negative Precision: {}%'.format(precision2 * 100))
            print('Negative Recall: {}%'.format(recall2 * 100))
            print('Negative F1-Score: {}%'.format(f1_2 * 100))
        elif verbose and num == 3:
            print('Evaluation Metrics:')
            print('Accuracy: {}%'.format(accuracy * 100))
            print('Positive Precision: {}%'.format(precision1 * 100))
            print('Positive Recall: {}%'.format(recall1 * 100))
            print('Positive F1-Score: {}%'.format(f1_1 * 100))
            print('Negative Precision: {}%'.format(precision2 * 100))
            print('Negative Recall: {}%'.format(recall2 * 100))
            print('Negative F1-Score: {}%'.format(f1_2 * 100))
            print('Neutral Precision: {}%'.format(precision3 * 100))
            print('Neutral Recall: {}%'.format(recall3 * 100))
            print('Neutral F1-Score: {}%'.format(f1_3 * 100))
        elif verbose and num == 5:
            print('Evaluation Metrics:')
            print('Accuracy: {}%'.format(accuracy * 100))
            print('One Star Precision: {}%'.format(precision1 * 100))
            print('One Star Recall: {}%'.format(recall1 * 100))
            print('One Star F1-Score: {}%'.format(f1_1 * 100))
            print('Two Star Precision: {}%'.format(precision2 * 100))
            print('Two Star Recall: {}%'.format(recall2 * 100))
            print('Two Star F1-Score: {}%'.format(f1_2 * 100))
            print('Three Star Precision: {}%'.format(precision3 * 100))
            print('Three Star Recall: {}%'.format(recall3 * 100))
            print('Three Star F1-Score: {}%'.format(f1_3 * 100))
            print('Four Star Precision: {}%'.format(precision4 * 100))
            print('Four Star Recall: {}%'.format(recall4 * 100))
            print('Four Star F1-Score: {}%'.format(f1_4 * 100))
            print('Five Star Precision: {}%'.format(precision5 * 100))
            print('Five Star Recall: {}%'.format(recall5 * 100))
            print('Five Star F1-Score: {}%'.format(f1_5 * 100))

        """
        if self.classifier_type == 'nn':
            score = self.model.evaluate(
                test_data, np.array(test_target), verbose=0)[1]
        """
        if num == 2:
            return accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2
        if num == 3:
            return accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2, precision3, recall3, f1_3
        if num == 5:
            return accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2, precision3, recall3, f1_3, precision4, recall4, f1_4, precision5, recall5, f1_5

    def evaluate_average_accuracy(self, reviews_filename, n_folds, num=2, verbose=False):
        """ Use stratified k fold to calculate average accuracy of models

        Args:
            reviews_filename: Filename of CSV with reviews to train on
            n_folds: int, number of k-folds
            verbose: Whether or not to print evaluation metrics to console
        """

        data, target, info = self.preprocess(reviews_filename, num)
        splits = StratifiedKFold(n_splits=n_folds)
        accuracies, class_1_precisions, class_1_recalls, class_1_f1s = [], [], [], []
        class_2_precisions, class_2_recalls, class_2_f1s = [], [], []
        if num == 3:
            class_3_precisions, class_3_recalls, class_3_f1s = [], [], []
        if num == 5:
            class_3_precisions, class_3_recalls, class_3_f1s = [], [], []
            class_4_precisions, class_4_recalls, class_4_f1s = [], [], []
            class_5_precisions, class_5_recalls, class_5_f1s = [], [], []
        for train, test in splits.split(data, target):
            x_train = [data[x] for x in train]
            y_train = [target[x] for x in train]
            x_test = [data[x] for x in test]
            y_test = [target[x] for x in test]

            model = self.generate_model()
            model.fit(x_train, y_train)
            if num == 2:
                accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2 = self.evaluate_accuracy(x_test,
                                                                                                    y_test, num,
                                                                                                    model=model)
            if num == 3:
                accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2, precision3, recall3, f1_3 = self.evaluate_accuracy(x_test,
                                                                                                    y_test, num,
                                                                                                    model=model)
            if num == 5:
                accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2, precision3, recall3, f1_3, precision4, recall4, f1_4, precision5, recall5, f1_5 = self.evaluate_accuracy(x_test,
                                                                                                                                                            y_test, num,
                                                                                                                                                            model=model)
            accuracies.append(accuracy)
            class_1_precisions.append(precision1)
            class_2_precisions.append(precision2)
            class_1_recalls.append(recall1)
            class_2_recalls.append(recall2)
            class_1_f1s.append(f1_1)
            class_2_f1s.append(f1_2)
            if num == 3 or num == 5:
                class_3_precisions.append(precision3)
                class_3_recalls.append(recall3)
                class_3_f1s.append(f1_3)
            if num == 5:
                class_4_precisions.append(precision4)
                class_4_recalls.append(recall4)
                class_4_f1s.append(f1_4)
                class_5_precisions.append(precision5)
                class_5_recalls.append(recall5)
                class_5_f1s.append(f1_5)
        average_accuracy = np.mean(np.array(accuracies)) * 100
        average_precision1 = np.mean(np.array(class_1_precisions)) * 100
        average_precision2 = np.mean(np.array(class_2_precisions)) * 100
        average_recall1 = np.mean(np.array(class_1_recalls)) * 100
        average_recall2 = np.mean(np.array(class_2_recalls)) * 100
        average_f1_1 = np.mean(np.array(class_1_f1s)) * 100
        average_f1_2 = np.mean(np.array(class_2_f1s)) * 100
        if num == 3 or num == 5:
            average_precision3 = np.mean(np.array(class_3_precisions)) * 100
            average_recall3 = np.mean(np.array(class_3_recalls)) * 100
            average_f1_3 = np.mean(np.array(class_3_f1s)) * 100
        if num == 5:
            average_precision4 = np.mean(np.array(class_4_precisions)) * 100
            average_recall4 = np.mean(np.array(class_4_recalls)) * 100
            average_f1_4 = np.mean(np.array(class_4_f1s)) * 100
            average_precision5 = np.mean(np.array(class_5_precisions)) * 100
            average_recall5 = np.mean(np.array(class_5_recalls)) * 100
            average_f1_5 = np.mean(np.array(class_5_f1s)) * 100
        if num == 2:
            metrics_ = {'accuracies': accuracies, 'positive_precisions': class_1_precisions,
                        'positive_recalls': class_1_recalls, 'positive_f1_scores': class_1_f1s,
                        'negative_precisions': class_2_precisions, 'negative_recalls': class_2_recalls,
                        'negative_f1_scores': class_2_f1s, 'average_accuracy': average_accuracy,
                        'average_positive_precision': average_precision1, 'average_positive_recall': average_recall1,
                        'average_positive_f1_score': average_f1_1, 'average_negative_precision': average_precision2,
                        'average_negative_recall': average_recall2, 'average_negative_f1_score': average_f1_2}
        if num == 3:
            metrics_ = {'accuracies': accuracies, 'positive_precisions': class_1_precisions,
                        'positive_recalls': class_1_recalls, 'positive_f1_scores': class_1_f1s,
                        'negative_precisions': class_2_precisions, 'negative_recalls': class_2_recalls,
                        'negative_f1_scores': class_2_f1s, 'average_accuracy': average_accuracy,
                        'average_positive_precision': average_precision1, 'average_positive_recall': average_recall1,
                        'average_positive_f1_score': average_f1_1, 'average_negative_precision': average_precision2,
                        'average_negative_recall': average_recall2, 'average_negative_f1_score': average_f1_2, 
                        'neutral_precisions': class_3_precisions, 'neutral_recalls': class_3_recalls, 'neutral_f1_scores': class_3_f1s, 'average_neutral_precision': average_precision3,
                        'average_neutral_recall': average_recall3, 'average_neutral_f1_score': average_f1_3}    
        if num == 5:
            metrics_ = {'accuracies': accuracies, 'onestar_precisions': class_1_precisions,
                        'onestar_recalls': class_1_recalls, 'onestar_f1_scores': class_1_f1s,
                        'twostar_precisions': class_2_precisions, 'twostar_recalls': class_2_recalls,
                        'twostar_f1_scores': class_2_f1s, 'average_accuracy': average_accuracy,
                        'average_onestar_precision': average_precision1, 'average_onestar_recall': average_recall1,
                        'average_onestar_f1_score': average_f1_1, 'average_twostar_precision': average_precision2,
                        'average_twostar_recall': average_recall2, 'average_twostar_f1_score': average_f1_2, 
                        'threestar_precisions': class_3_precisions, 'threestar_recalls': class_3_recalls, 
                        'threestar_f1_scores': class_3_f1s, 'average_threestar_precision': average_precision3,
                        'average_threestar_recall': average_recall3, 'average_threestar_f1_score': average_f1_3, 
                        'fourstar_precisions': class_4_precisions, 'fourstar_recalls': class_4_recalls, 
                        'fourstar_f1_scores': class_4_f1s, 'average_fourstar_precision': average_precision4,
                        'average_fourstar_recall': average_recall4, 'average_fourstar_f1_score': average_f1_4, 
                        'fivestar_precisions': class_5_precisions, 'fivestar_recalls': class_5_recalls, 
                        'fivestar_f1_scores': class_5_f1s, 'average_fivestar_precision': average_precision5,
                        'average_fivestar_recall': average_recall5, 'average_fivestar_f1_score': average_f1_5}
        if verbose and num == 2:
            print('Validation Metrics:')
            print('Average Accuracy: {}%'.format(average_accuracy))
            print('Average Class 1 (Positive) Precision: {}%'.format(average_precision1))
            print('Average Class 1 (Positive) Recall: {}%'.format(average_recall1))
            print('Average Class 1 (Positive) F1-Score: {}%'.format(average_f1_1))
            print('Average Class 2 (Negative) Precision: {}%'.format(average_precision2))
            print('Average Class 2 (Negative) Recall: {}%'.format(average_recall2))
            print('Average Class 2 (Negative) F1-Score: {}%'.format(average_f1_2))
        if verbose and num == 3:
            print('Validation Metrics:')
            print('Average Accuracy: {}%'.format(average_accuracy))
            print('Average Class 1 (Positive) Precision: {}%'.format(average_precision1))
            print('Average Class 1 (Positive) Recall: {}%'.format(average_recall1))
            print('Average Class 1 (Positive) F1-Score: {}%'.format(average_f1_1))
            print('Average Class 2 (Negative) Precision: {}%'.format(average_precision2))
            print('Average Class 2 (Negative) Recall: {}%'.format(average_recall2))
            print('Average Class 2 (Negative) F1-Score: {}%'.format(average_f1_2))
            print('Average Class 3 (Neutral) Precision: {}%'.format(average_precision3))
            print('Average Class 3 (Neutral) Recall: {}%'.format(average_recall3))
            print('Average Class 3 (Neutral) F1-Score: {}%'.format(average_f1_3))
        if verbose and num == 5:
            print('Evaluation Metrics:')
            print('Average Accuracy: {}%'.format(average_accuracy))
            print('Average One Star Precision: {}%'.format(average_precision1))
            print('Average One Star Recall: {}%'.format(average_recall1))
            print('Average One Star F1-Score: {}%'.format(average_f1_1))
            print('Average Two Star Precision: {}%'.format(average_precision2))
            print('Average Two Star Recall: {}%'.format(average_recall2))
            print('Average Two Star F1-Score: {}%'.format(average_f1_2))
            print('Average Three Star Precision: {}%'.format(average_precision3))
            print('Average Three Star Recall: {}%'.format(average_recall3))
            print('Average Three Star F1-Score: {}%'.format(average_f1_3))
            print('Average Four Star Precision: {}%'.format(average_precision4))
            print('Average Four Star Recall: {}%'.format(average_recall4))
            print('Average Four Star F1-Score: {}%'.format(average_f1_4))
            print('Average Five Star Precision: {}%'.format(average_precision5))
            print('Average Five Star Recall: {}%'.format(average_recall5))
            print('Average Five Star F1-Score: {}%'.format(average_f1_5))
        return metrics_

    def classify(self, output_file, num=2, csv_file=None, text_file=None, evaluate=False):
        """Classifies a list of comments as positive or negative

        Args:
            output_file: txt file to which classification results will output
            csv_file: CSV file with comments to classify
            text_file: txt file with comments and no ratings
            evaluate: whether or not to write evaluation metrics to output file
        """

        if self.model is None:
            raise Exception('Model needs training first')
        if self.model and not self.vectorizer:
            raise Exception('A model must be trained before classifying')
        if text_file and evaluate:
            raise Exception('In order to evaluate the classification, data must be passed in csv format')

        stop_words = set(stopwords.words('english'))
        tokenizer = RegexpTokenizer(r'\w+')
        df = pd.read_csv(csv_file)

        clean_comments = []
        comments = []
        target = []

        if num == 2:
            for review in df.itertuples():
                if type(review.comment) == float or self.negative_threshold < review.rating < self.positive_threshold:
                    continue
                elif review.rating <= self.negative_threshold:
                    rating = 0
                else:
                    rating = 1
                comments.append(review.comment)
                clean_comments.append(' '.join(word.lower() for word in tokenizer.tokenize(review.comment)
                                            if word not in stop_words))
                target.append(rating)
        if num == 3:
            for review in df.itertuples():
                if type(review.comment) == float:
                    continue
                elif self.negative_threshold < review.rating < self.positive_threshold:
                    rating = 1
                elif review.rating <= self.negative_threshold:
                    rating = 0
                else:
                    rating = 2
                comments.append(review.comment)
                clean_comments.append(' '.join(word.lower() for word in tokenizer.tokenize(review.comment)
                                            if word not in stop_words))
                target.append(rating)
        if num == 5:
            for review in df.itertuples():
                if type(review.comment) == float:
                    continue
                if review.rating == 1.0:
                    rating = 1
                elif review.rating == 2.0:
                    rating = 2
                elif review.rating == 3.0:
                    rating = 3
                elif review.rating == 4.0:
                    rating = 4
                else:
                    rating = 5
                comments.append(review.comment)
                clean_comments.append(' '.join(word.lower() for word in tokenizer.tokenize(review.comment)
                                            if word not in stop_words))
                target.append(rating)
        data = np.array([self.vectorizer.transform([comment]).toarray() for comment in clean_comments]).squeeze(1)
        predictions = self.model.predict(data)

        classifications_file = open(output_file, 'a')
        if num == 2: 
            for i, comment in enumerate(comments):
                if predictions[i] == 1:
                    pred = 'Positive'
                else:
                    pred = 'Negative'
                if target[i] == 0:
                    actual = 'Negative'
                else:
                    actual = 'Positive'
                classifications_file.write('Comment: {}\tPrediction: {}\tActual Rating: {}\n'.format(comment, pred, actual))
        if num == 3:
            for i, comment in enumerate(comments):
                if predictions[i] == 2:
                    pred = 'Positive'
                elif predictions[i] == 1:
                    pred = 'Neutral'
                else:
                    pred = 'Negative'
                if target[i] == 0:
                    actual = 'Negative'
                elif target[i] == 1:
                    actual = 'Neutral'
                else:
                    actual = 'Positive'
                classifications_file.write('Comment: {}\tPrediction: {}\tActual Rating: {}\n'.format(comment, pred, actual))
        if num == 5:
            for i, comment in enumerate(comments):
                if predictions[i] == 1:
                    pred = 'One Star'
                elif predictions[i] == 2:
                    pred = 'Two Star'
                elif predictions[i] == 3:
                    pred = 'Three Star'
                elif predictions[i] == 4:
                    pred = 'Four Star'
                else:
                    pred = 'Five Star'
                if target[i] == 1:
                    actual = 'One Star'
                elif target[i] == 2:
                    actual = 'Two Star'
                elif target[i] == 3:
                    actual = 'Three Star'
                elif target[i] == 4:
                    actual = 'Four Star'
                else:
                    actual = 'Five Star'
                classifications_file.write('Comment: {}\tPrediction: {}\tActual Rating: {}\n'.format(comment, pred, actual))
        if evaluate and num == 2:
            accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2 = metrics(target, predictions)
            classifications_file.write('\nEvaluation Metrics:\n')
            classifications_file.write('Accuracy: {}%\nClass 1 (Positive) Precision: {}%\n'
                                       'Class 1 (Positive) Recall: {}%\nClass 1 (Positive) F1-Measure: {}%\n'
                                       'Class 2 (Negative) Precision: {}%\nClass 2 (Negative) Recall: {}%\n'
                                       'Class 2 (Negative) F1-Measure: {}%'.format(accuracy * 100, precision1 * 100,
                                                                                   recall1 * 100, f1_1 * 100,
                                                                                   precision2 * 100, recall2 * 100,
                                                                                   f1_2 * 100))
        if evaluate and num == 3:
            accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2, precision3, recall3, f1_3 = metrics(target, predictions)
            classifications_file.write('\nEvaluation Metrics:\n')
            classifications_file.write('Accuracy: {}%\nClass 1 (Positive) Precision: {}%\n'
                                       'Class 1 (Positive) Recall: {}%\nClass 1 (Positive) F1-Measure: {}%\n'
                                       'Class 2 (Negative) Precision: {}%\nClass 2 (Negative) Recall: {}%\n'
                                       'Class 2 (Negative) F1-Measure: {}%\nClass 3 (Neutral) Precision: {}%\n'
                                       'Class 3 (Neutral) Recall: {}%\nClass 3 (Neutral) F1-Measure: {}%\n'.format(accuracy * 100, precision1 * 100,
                                                                                   recall1 * 100, f1_1 * 100,
                                                                                   precision2 * 100, recall2 * 100,
                                                                                   f1_2 * 100, precision3 * 100, recall3 * 100, f1_3 * 100))
        if evaluate and num == 5:
            accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2, precision3, recall3, f1_3, precision4, recall4, f1_4, precision5, recall5, f1_5 = metrics(target, predictions)
            classifications_file.write('\nEvaluation Metrics:\n')
            classifications_file.write('Accuracy: {}%\nOne Star Precision: {}%\n'
                                       'One Star Recall: {}%\nOne Star F1-Measure: {}%\n'
                                       'Two Star Precision: {}%\nTwo Star Recall: {}%\n'
                                       'Two Star F1-Measure: {}%\nThree Star Precision: {}%\n'
                                       'Three Star Recall: {}%\nThree Star F1-Measure: {}%\n'
                                       'Four Star Precision: {}%\nFour Star Recall: {}%\n'
                                       'Four Star F1-Measure: {}%\nFive Star Precision: {}%\n'
                                       'Five Star Recall: {}%\nFive Star F1-Measure: {}%\n'.format(accuracy * 100, precision1 * 100,
                                                                                   recall1 * 100, f1_1 * 100,
                                                                                   precision2 * 100, recall2 * 100,
                                                                                   f1_2 * 100, precision3 * 100, recall3 * 100, f1_3 * 100, precision4 * 100, recall4 * 100, f1_4 * 100, precision5 * 100, recall5 * 100, f1_5 * 100))

    def save_model(self, output_file):
        """ Saves a trained model to a file
        """

        with open(output_file, 'wb') as pickle_file:
            pickle.dump(self.model, pickle_file, protocol=pickle.HIGHEST_PROTOCOL)
            pickle.dump(self.vectorizer, pickle_file, protocol=pickle.HIGHEST_PROTOCOL)

        """
        elif self.classifier_type == 'nn':
            with open("trained_nn_model.json", "w") as json_file:
                json_file.write(self.model.to_json()) # Save mode
            self.model.save_weights("trained_nn_weights.h5") # Save weights
            with open('trained_nn_vec_encoder.pickle', 'wb') as pickle_file:
                pickle.dump(self.vectorizer, pickle_file)
                pickle.dump(self.encoder, pickle_file)
            tar_file = tarfile.open("trained_nn_model.tar", 'w')
            tar_file.add('trained_nn_model.json')
            tar_file.add('trained_nn_weights.h5')
            tar_file.add('trained_nn_vec_encoder.pickle')
            tar_file.close()

            os.remove('trained_nn_model.json')
            os.remove('trained_nn_weights.h5')
            os.remove('trained_nn_vec_encoder.pickle')
        """

    def load_model(self, model_file=None, tar_file=None, saved_vectorizer=None):
        """ Loads a trained model from a file
        """

        with open(model_file, 'rb') as model_file:
            self.model = pickle.load(model_file)
            self.vectorizer = pickle.load(model_file)

        """
        if saved_vectorizer and tar_file:
            tfile = tarfile.open(tar_file, 'r')
            tfile.extractall()
            tfile.close()

            with open('trained_nn_model.json', 'r') as json_model:
                loaded_model = json_model.read()
                self.model = model_from_json(loaded_model)

            self.model.load_weights('trained_nn_weights.h5')
            self.model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
            with open('trained_nn_vec_encoder.pickle', 'rb') as pickle_file:
                self.vectorizer = pickle.load(pickle_file)

            os.remove('trained_nn_model.json')
            os.remove('trained_nn_weights.h5')
        """


def metrics(actual_ratings, predicted_ratings, num=2):
    if num == 2:
        matrix = confusion_matrix(actual_ratings, predicted_ratings)
        tn, fp, fn, tp = matrix[0][0], matrix[0, 1], matrix[1, 0], matrix[1][1]
        accuracy = (tp + tn) * 1.0 / (tp + tn + fp + fn)
        precision1, precision2 = (tp * 1.0) / (tp + fp), (tn * 1.0) / (tn + fn)
        recall1, recall2 = (tp * 1.0) / (tp + fn), (tn * 1.0) / (tn + fp)
        f1_1 = 2 * ((precision1 * recall1) / (precision1 + recall1))
        f1_2 = 2 * ((precision2 * recall2) / (precision2 + recall2))

        return accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2
    if num == 3:
        matrix = confusion_matrix(actual_ratings, predicted_ratings)
        tpPos, tpNeg, tpNeu, fBA, fBC, fAB, fCB, fCA, fAC = matrix[0][0], matrix[1, 1], matrix[2, 2], matrix[1, 0], matrix[1, 2], matrix[0, 1], matrix[2][1], matrix[2,0], matrix[0,2]
        # print(tpPos + tpNeg + tpNeu)
        accuracy = ((tpPos + tpNeg + tpNeu) * 1.0) / (tpPos + tpNeg + tpNeu + fBA + fBC + fAB + fCB + fCA + fAC)
        precision1, precision2, precision3 = (tpPos * 1.0) / (tpPos + fBA + fCA), (tpNeg * 1.0) / (tpNeg + fAB + fCB), (tpNeu * 1.0) / (tpNeu + fBC + fAC)
        recall1, recall2, recall3 = (tpPos * 1.0) / (tpPos + fAB + fAC), (tpNeg * 1.0) / (tpNeg + fBA + fBC), (tpNeu * 1.0) / (tpNeu + fCA + fCB) 
        f1_1 = 2 * ((precision1 * recall1) / (precision1 + recall1))
        f1_2 = 2 * ((precision2 * recall2) / (precision2 + recall2))
        f1_3 = 2 * ((precision3 * recall3) / (precision3 + recall3))

        return accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2, precision3, recall3, f1_3
    if num == 5:
        matrix = confusion_matrix(actual_ratings, predicted_ratings)
        tpOneStar, tpTwoStar, tpThreeStar, tpFourStar, tpFiveStar, fAB, fAC, fAD, fAE, fBA, fBC, fBD, fBE, fCA, fCB, fCD, fCE, fDA, fDB, fDC, fDE, fEA, fEB, fEC, fED = matrix[0, 0], matrix[1, 1], matrix[2, 2], matrix[3, 3], matrix[4, 4],  matrix[0, 1], matrix[0, 2], matrix[0, 3], matrix[0, 4], matrix[1, 0], matrix[1, 2], matrix[1, 3], matrix[1, 4], matrix[2, 0], matrix[2, 1], matrix[2, 3], matrix[2, 4], matrix[3, 0], matrix[3, 1], matrix[3, 2], matrix[3, 4], matrix[4, 0], matrix[4, 1], matrix[4, 2], matrix[4, 3]
        accuracy = ((tpOneStar + tpTwoStar + tpThreeStar + tpFourStar + tpFiveStar) * 1.0) / (tpOneStar + tpTwoStar + tpThreeStar + tpFourStar + tpFiveStar + fAB + fAC + fAD + fAE + fBA + fBC + fBD + fBE + fCA + fCB + fCD + fCE + fDA + fDB + fDC + fDE + fEA + fEB + fEC + fED)
        precision1, precision2, precision3, precision4, precision5 = (tpOneStar * 1.0) / (tpOneStar + fBA + fCA + fDA + fEA), (tpTwoStar * 1.0) / (tpTwoStar + fAB + fCB + fDB + fEB), (tpThreeStar * 1.0) / (tpThreeStar + fAC + fBC + fDC + fEC), (tpFourStar * 1.0) / (tpFourStar + fAD + fBD + fCD + fED), (tpFiveStar * 1.0) / (tpFiveStar + fAE + fBE + fCE + fDE)
        recall1, recall2, recall3, recall4, recall5 = (tpOneStar * 1.0) / (tpOneStar + fAB + fAC + fAD + fAE), (tpTwoStar * 1.0) / (tpTwoStar + fBA + fBC + fBD + fBE), (tpThreeStar * 1.0) / (tpThreeStar + fCA + fCB + fCD + fCE), (tpFourStar * 1.0) / (tpFourStar + fDA + fDB + fDC + fDE), (tpFiveStar * 1.0) / (tpFiveStar + fEA + fEB + fEC + fED)
        f1_1 = 2 * ((precision1 * recall1) / (precision1 + recall1))
        # print('precision: ' + str(precision2))
        # print('recall: ' + str(recall2))
        # print('sum: ' + str(recall2 + precision2))
        if precision2 + recall2 == 0:
            f1_2 = 0
        else:
            f1_2 = 2 * ((precision2 * recall2) / (precision2 + recall2))
        # print('f1 score: ' + str(f1_2))
        f1_3 = 2 * ((precision3 * recall3) / (precision3 + recall3))
        f1_4 = 2 * ((precision4 * recall4) / (precision4 + recall4))
        f1_5 = 2 * ((precision5 * recall5) / (precision5 + recall5))
        

        return accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2, precision3, recall3, f1_3, precision4, recall4, f1_4, precision5, recall5, f1_5

"""
This is the code for the command line tool. It's not yet up and running yet, but it will be soon!
# TODO finish command line tool

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('--nb', help='Use Naive Bayes classifier (SciKit Learn MultinomialNaiveBayes Implementation)',
                        action='store_true')
    parser.add_argument('--rf', help='Use Random Forest classifier (SciKit Learn Implementation)',
                        action='store_true')
    parser.add_argument('--svm', help='Use Support Vector Machine classifier (SciKit Learn LinearSVC Implementation)',
                        action='store_true')
    parser.add_argument('-p', '--process', help='File path to reviews csv to process')
    parser.add_argument('-f', '--fit', help='File path to reviews csv to fit model with')
    parser.add_argument('-e', '--evaluate', help='Path to reviews file to evaluate model on')
    parser.add_argument('-v', '--validate', help='Path to reviews file on which to perform k-fold cross validation')
    parser.add_argument('-k', '--folds', help='Number of folds for cross-validation (default 10)', type=int)
    parser.add_argument('-c', '--classify', help='Path of reviews file to classify')
    parser.add_argument('--cf', help='Classification output file')
    parser.add_argument('-s', '--save', help='File to which to save trained model')
    parser.add_argument('-l', '--load', help='Path to saved model file')
    parser.add_argument('-w', '--write', help='Path to write output file with information')

    args = parser.parse_args()
    info = {'start_datetime': str(datetime.datetime.now())}
    start = time()

    classifier_type = None
    if args.nb:
        classifier_type = 'nb'
    elif args.svm:
        classifier_type = 'svm'
    elif args.rf:
        classifier_type = 'rf'
    classifier = ReviewClassifier(classifier_type=classifier_type)
    info['classifier_type'] = classifier_type

    if args.evaluate and not args.load and not args.fit:
        raise Exception('In order to evaluate, you must specify a model to '
                        'load (-l flag) or fit a model (-f flag)')
    if args.classify and not args.load and not args.fit:
        raise Exception('In order to classify, you must specify a model to '
                        'load (-l flag) or fit a model (-f flag)')
    if args.classify and not args.cf:
        raise Exception('In order to classify, you must specify and classification'
                        ' output file (using the --cf flag)')

    if args.process:
        data, target, preprocess_info = classifier.preprocess(args.process)
        info['num_positive_reviews'] = preprocess_info['positive']
        info['num_negative_reviews'] = preprocess_info['negative']
        info['num_neutral_reviews'] = preprocess_info['neutral']

    if args.load:
        classifier.load_model(args.load)

    if classifier.model and args.evaluate:
        data, target, data_info = classifier.preprocess(args.evaluate)
        accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2 = classifier.evaluate_accuracy(data, target)
        info['eval_accuracy'] = accuracy
        info['class_1_precision'] = precision1
        info['class_1_recall'] = recall1
        info['class_1_f1'] = f1_1
        info['class_2_precision'] = precision2
        info['class_2_recall'] = recall2
        info['class_2_f1'] = f1_2

    if classifier.model and args.classify:
        classifier.classify(output_file=args.cf, csv_file=args.classify)

    if args.fit and not classifier.model:
        data, target, data_info = classifier.preprocess(args.fit)
        classifier.fit(data, target)

    if args.fit and classifier.model:
        warnings.warn('You are trying to both load and fit a model. The loaded model takes precedence, '
                      'and a model will not be fit.')

    if args.evaluate and not args.load:
        data, target, data_info = classifier.preprocess(args.evaluate)
        accuracy, precision1, recall1, f1_1, precision2, recall2, f1_2 = classifier.evaluate_accuracy(data, target)
        info['eval_accuracy'] = accuracy
        info['class_1_precision'] = precision1
        info['class_1_recall'] = recall1
        info['class_1_f1'] = f1_1
        info['class_2_precision'] = precision2
        info['class_2_recall'] = recall2
        info['class_2_f1'] = f1_2

    if args.validate:
        folds = 10
        if args.folds:
            folds = args.folds
        evaluation_info = classifier.evaluate_average_accuracy(args.evaluate, folds)
        info['k-fold validation results'] = evaluation_info

    if args.save:
        classifier.save_model(args.save)

    info['end_datetime'] = str(datetime.datetime.now())
    end = time()
    elapsed = float(end - start)
    info['time_elapsed'] = elapsed

    if args.write:
        with open(args.write + '.json', 'w') as output:
            json.dump(info, output, indent=2)


if __name__ == '__main__':
    main()
"""


