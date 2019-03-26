import string

from nltk.corpus import stopwords
from nltk.stem.porter import *

from sklearn.feature_extraction.text import TfidfVectorizer


class TextSimilarityCalculator:
    def __init__(self, ):
        self.tfidf_vectorizer = TfidfVectorizer(analyzer=self.text_process)

    @staticmethod
    def text_process(string_variable):
        """
        Takes in a string of text, then performs the following:
        1. Remove all punctuation
        2. Remove all stopwords
        3. Returns a list of the cleaned text
        """
        # Check characters to see if they are in punctuation
        no_punctuation = [char for char in string_variable if char not in string.punctuation]

        # Join the characters again to form the string.
        no_punctuation = ''.join(no_punctuation)

        # Now just remove any stopwords
        before_stem = [word for word in no_punctuation.split() if word.lower() not in stopwords.words('english')]

        stemmer = PorterStemmer()
        return [stemmer.stem(word) for word in before_stem]

    def cos_similarity(self,string1, string2):
        term_frequency = self.tfidf_vectorizer.fit_transform([string1, string2])
        return (term_frequency * term_frequency.T).A[0, 1]

    @staticmethod
    def add_text_similarity_ranking(data_frame):
        # data_frame['text_similarity'] = data_frame['cos_title'] + data_frame['cos_description']
        data_frame["text_rank"] = data_frame["text_similarity"].rank(method='min', ascending=False)
