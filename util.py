from typing import Set
import pandas as pd
import time
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

def compute_prediction(concepts: list, predictor) -> list[dict]:
    res = []
    for c in concepts:
        start_time = time.time()
        y = predictor.predict(concept=c)
        runtime = time.time() - start_time
        res.append({'Concept': c, 'Individuals': y, f'RT': runtime, 'Name': predictor.name})
    return res


def evaluate_results(true_results: list[dict], predictions: list[dict]) -> pd.DataFrame:
    results = []
    for y_results, yhat_results in zip(true_results, predictions):
        assert y_results['Concept'] == yhat_results['Concept']
        concept = y_results['Concept']
        concept_size = len(y_results['Individuals'])

        y = y_results['Individuals']
        yhat = yhat_results['Individuals']
        sim = jaccard_similarity(y=y, yhat=yhat)
        results.append({'Concept': concept.str, 'ConceptSize': concept_size, 'Similarity': sim,
                        f'RT{y_results["Name"]}': y_results['RT'],
                        f'RT{yhat_results["Name"]}': yhat_results['RT']})

    return pd.DataFrame(results)

