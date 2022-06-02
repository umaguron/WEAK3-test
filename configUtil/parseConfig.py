import configparser
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("inputIni", 
            help="fullpath of toughInput setting input.ini", type=str)
parser.add_argument("section", 
            help="fullpath of toughInput setting input.ini", type=str)
parser.add_argument("keyName", 
            help="fullpath of toughInput setting input.ini", type=str)
args = parser.parse_args()
config = configparser.ConfigParser()
config.read(args.inputIni)
print(config[args.section][args.keyName])
