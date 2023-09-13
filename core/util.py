def compute_prediction(concepts: list, predictor) -> list[dict]:
    res = []
    for c in concepts:
        start_time = time.time()
        y = predictor.predict(concept=c)
        runtime = time.time() - start_time
        res.append({'Concept': c, 'Individuals': y, f'RT': runtime, 'Name': predictor.name})
    return res