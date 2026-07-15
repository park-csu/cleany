from cleany_perception.detector import Detection, parse_boxes


def test_parse_boxes_maps_class_ids_to_labels():
    boxes = [(10.0, 20.0, 30.0, 40.0)]
    scores = [0.9]
    class_ids = [41]
    names = {41: 'cup', 39: 'bottle'}

    dets = parse_boxes(boxes, scores, class_ids, names)

    assert dets == [Detection(label='cup', score=0.9, x1=10.0, y1=20.0, x2=30.0, y2=40.0)]


def test_parse_boxes_handles_multiple_detections():
    boxes = [(0.0, 0.0, 5.0, 5.0), (1.0, 2.0, 3.0, 4.0)]
    scores = [0.5, 0.8]
    class_ids = [39, 60]
    names = {39: 'bottle', 60: 'dining table'}

    dets = parse_boxes(boxes, scores, class_ids, names)

    assert [d.label for d in dets] == ['bottle', 'dining table']
    assert [d.score for d in dets] == [0.5, 0.8]


def test_parse_boxes_falls_back_to_stringified_id_for_unknown_class():
    dets = parse_boxes([(0.0, 0.0, 1.0, 1.0)], [0.3], [999], {41: 'cup'})

    assert dets[0].label == '999'


def test_parse_boxes_empty_input_returns_empty_list():
    assert parse_boxes([], [], [], {}) == []


def test_parse_boxes_casts_values_to_float():
    dets = parse_boxes([(1, 2, 3, 4)], [1], [41], {41: 'cup'})

    d = dets[0]
    assert isinstance(d.score, float)
    assert (d.x1, d.y1, d.x2, d.y2) == (1.0, 2.0, 3.0, 4.0)
