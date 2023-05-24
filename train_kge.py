from dicee import KGE, Execute
from dicee.config import Args

# (1) Load Default Params
args = Args()
# (2) Select a Dataset and a KGE
args.path_dataset_folder = "KGs/Family"
args.model = "AConEx"
args.embedding_dim = 128
args.num_epochs = 500
args.num_of_output_channels = 3
args.batch_size = 1024
# NegSample leads to better results than KvsAll, KvsSample and 1vsAll do
args.scoring_technique = "NegSample"
args.neg_ratio = 10
args.eval_model = "train_val_test"
report = Execute(args).start()
"""
Done ! It took 7.850 minutes.

*** Save Trained Model ***
Took 0.0023 seconds | Current Memory Usage  619.32 in MB
Total computation time: 471.016 seconds
Evaluate AConEx on Train set
Num of triples 2033
** Evaluation without batching
{'H@1': 0.999508116084604, 'H@3': 1.0, 'H@10': 1.0, 'MRR': 0.999754058042302}

"""