from typing import Set
def jaccard_similarity(y: Set[str], yhat: Set[str])->float:
    """
    Compute Jaccard Similarity
    :param y: A set of URIs
    :param yhat: A set of URIs
    :return:
    """
    if len(yhat)==len(y)==0:
        return 1.0
    if len(yhat) ==0 or len(y)==0:
        return 0.0
    return len(y.intersection(yhat)) / len(y.union(yhat))
