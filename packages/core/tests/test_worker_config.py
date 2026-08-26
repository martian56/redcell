from redcell_core.config import Settings


def test_worker_max_jobs_default_and_override():
    assert Settings().worker_max_jobs == 10
    assert Settings(worker_max_jobs=4).worker_max_jobs == 4
