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
Epoch:500 | Loss:0.15082803 | Runtime:0.003 mins
Done ! It took 1.257 minutes.

*** Save Trained Model ***
Took 0.0016 seconds | Current Memory Usage  543.2 in MB
Total computation time: 75.473 seconds
Evaluate AConEx on Train set
Num of triples 2033
** Evaluation without batching
{'H@1': 0.9965568125922283, 'H@3': 0.999754058042302, 'H@10': 1.0, 'MRR': 0.9979778105700389}

"""
