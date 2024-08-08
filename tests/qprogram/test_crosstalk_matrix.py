from qililab.qprogram.crosstalk_matrix import CrosstalkMatrix


class TestCrosstalkMatrix:
    """Unit tests checking the Calibration attributes and methods."""

    def test_init(self):
        """Test init method"""
        crosstalk_matrix = CrosstalkMatrix()

        assert isinstance(crosstalk_matrix, CrosstalkMatrix)
        assert isinstance(crosstalk_matrix.matrix, dict)
        assert len(crosstalk_matrix.matrix) == 0

    def test_set_get_methods(self):
        """Test __set_item__ and __get_item__ methods"""
        crosstalk_matrix = CrosstalkMatrix()
        crosstalk_matrix["bus1"]["bus2"] = 0.5

        assert isinstance(crosstalk_matrix["bus1"], dict)
        assert len(crosstalk_matrix["bus1"]) == 1
        assert crosstalk_matrix["bus1"]["bus2"] == 0.5

        crosstalk_matrix["bus2"] = {"bus1": 0.1}
        assert isinstance(crosstalk_matrix["bus2"], dict)
        assert len(crosstalk_matrix["bus2"]) == 1
        assert crosstalk_matrix["bus2"]["bus1"] == 0.1

    def test_str_method(self):
        """Test __str__ method"""
        crosstalk_matrix = CrosstalkMatrix()
        crosstalk_matrix["bus1"]["bus2"] = 0.5

        string = str(crosstalk_matrix)
        assert (
            string
            == """            bus1     bus2
bus1            \\      0.5
bus2          1.0        \\"""
        )

    def test_repr_method(self):
        """Test __repr__ method"""
        crosstalk_matrix = CrosstalkMatrix()
        crosstalk_matrix["bus1"]["bus2"] = 0.5

        representation = repr(crosstalk_matrix)
        assert representation == "CrosstalkMatrix({'bus1': {'bus2': 0.5}})"

    def test_from_buses_method(self):
        """Test from_buses class method"""
        crosstalk_matrix = CrosstalkMatrix.from_buses({"bus1", "bus2", "bus3"})

        assert isinstance(crosstalk_matrix, CrosstalkMatrix)
        assert isinstance(crosstalk_matrix.matrix, dict)

        assert "bus1" in crosstalk_matrix.matrix
        assert "bus2" in crosstalk_matrix.matrix["bus1"]
        assert "bus3" in crosstalk_matrix.matrix["bus1"]
        assert crosstalk_matrix["bus1"]["bus2"] == 1.0
        assert crosstalk_matrix["bus1"]["bus3"] == 1.0

        assert "bus2" in crosstalk_matrix.matrix
        assert "bus1" in crosstalk_matrix.matrix["bus2"]
        assert "bus3" in crosstalk_matrix.matrix["bus2"]
        assert crosstalk_matrix["bus2"]["bus1"] == 1.0
        assert crosstalk_matrix["bus2"]["bus3"] == 1.0

        assert "bus3" in crosstalk_matrix.matrix
        assert "bus1" in crosstalk_matrix.matrix["bus3"]
        assert "bus2" in crosstalk_matrix.matrix["bus3"]
        assert crosstalk_matrix["bus3"]["bus1"] == 1.0
        assert crosstalk_matrix["bus3"]["bus2"] == 1.0
