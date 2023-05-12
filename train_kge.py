from dicee import KGE, Execute
from dicee.config import Args
# (1) Load Default Params
args=Args()
# (2) Select a Dataset and a KGE
args.path_dataset_folder="KGs/Family"
args.model="AConEx"
args.embedding_dim=32
args.num_epochs=256
args.num_of_output_channels= 32
args.batch_size=1024
args.scoring_technique="KvsAll"
args.eval_model="train_val_test"
Execute(args).start()