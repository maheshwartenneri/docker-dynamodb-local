class DummyConfig:
    def __init__(self):
        self.cluster_scaling_configs = {
            "tables": {
                "table_name": "test-table",
                "scale_out_min_read_capacity": 1,
                "scale_out_max_read_capacity": 10,
                "scale_out_min_write_capacity": 1,
                "scale_out_max_write_capacity": 10
            }
        }