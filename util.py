def jaccard_similarity(y: Set[str], yhat: Set[str])->float:
    """
    Compute Jaccard Similarity
    :param y: A set of URIs
    :param yhat: A set of URIs
    :return:
    """
    return len(y.intersection(yhat)) / len(y.union(yhat))
