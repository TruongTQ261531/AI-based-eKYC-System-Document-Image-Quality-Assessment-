"""Run the frozen study unchanged except retrying its metadata writes."""
from research import fc_study, vlm_train
from research.fc_io import save_retry


def main():
    fc_study.save=save_retry
    vlm_train.save=save_retry
    fc_study.main()


if __name__=='__main__':main()
