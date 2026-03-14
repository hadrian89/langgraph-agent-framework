def analyze_trends(metrics):

    if len(metrics) < 3:
        return {}

    steps = [m.steps for m in metrics]
    sleep = [m.sleep_hours for m in metrics]

    trends = {}

    if steps[-1] < steps[0]:
        trends["steps_decline"] = True

    if sleep[-1] < sleep[0]:
        trends["sleep_decline"] = True

    if sum(sleep) / len(sleep) < 6:
        trends["sleep_deficit"] = True

    return trends
