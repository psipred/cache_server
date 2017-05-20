import requests
import sys
import hashlib
import subprocess
import shlex
import os.path
from Bio.Blast import NCBIXML
import time
import math
# arg 1 input fasta file
# arg 2 output dir
# arg 3 base uri
# arg 4 blast bin path
# arg 6 blast settings string
# arg 5 blast db

#
# python scripts/run_blast.py ./files/P04591.fasta ./files http://127.0.0.1:8000 /scratch0/NOT_BACKED_UP/dbuchan/Applications/ncbi-blast-2.2.31+/bin/ /scratch1/NOT_BACKED_UP/dbuchan/uniref/pdb_aa.fasta -num_iterations 20 -num_alignments 500 -num_threads 2
#
# python scripts/run_blast.py ./files/P04591.fasta ./files http://127.0.0.1:8000 /opt/ncbi-blast-2.5.0+/bin/ /opt/uniref/uniref90.fasta -num_iterations 20 -num_alignments 500 -num_threads 2


def read_file(path):
    seq = ''
    with open(path, 'r') as myfile:
        data = myfile.read()
    for line in data.split("\n"):
        if line.startswith(">"):
            continue
        line = line.rstrip()
        seq += line
    m = hashlib.md5()
    test_hash = m.update(seq.encode('utf-8'))
    return(m.hexdigest())


def get_num_alignments(path):
    hit_count = 0
    if os.path.isfile(path):
        result_handle = open(path)
        blast_records = NCBIXML.parse(result_handle)
        for record in blast_records:
            if len(record.alignments) > hit_count:
                hit_count = len(record.alignments)
    else:
        exit(1)

    return(hit_count)


def get_pssm_data(path):
    pssm_data = ""
    if os.path.isfile(path):
        with open(path) as myfile:
            pssm_data = myfile.read()
    else:
        exit(1)  # panic

    return(pssm_data)


fasta_file = sys.argv[1]  # path to input fasta
out_dir = sys.argv[2]  # path to place blast output and PSSM files
base_uri = sys.argv[3]  # ip or URI for the server blast_cache is running on
blast_bin = sys.argv[4]  # path to the blast binary dir
blast_db = sys.argv[5]  # path to blast db location
blast_settings = " ".join(sys.argv[6:])  # get everything else on the
#                                          commandline make it a string and
#                                          use it as the blast settings

# strings and data structures we need
seq_name = fasta_file.split("/")[-1].split(".")[0]
md5 = read_file(fasta_file)
entry_uri = base_uri+"/blast_cache/entry/"
entry_query = entry_uri+md5
i = iter(blast_settings.split())
request_data = dict(zip(i, i))

r = requests.get(entry_query, data=request_data)
if r.status_code == 404 and "No Record Available" in r.text:
    print("Running blast")
    cmd = blast_bin+"/psiblast -query "+fasta_file+" -out "+out_dir+"/" + \
        seq_name+".xml -out_pssm "+out_dir+"/"+seq_name+".pssm -db " + \
        blast_db+" -outfmt 5 "+blast_settings
    print(cmd)
    start_time = time.time()
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    p.wait()
    end_time = time.time()
    runtime = math.ceil(end_time-start_time)
    hit_count = get_num_alignments(out_dir+"/"+seq_name+".xml")
    pssm_data = get_pssm_data(out_dir+"/"+seq_name+".pssm")
    request_data["file_data"] = pssm_data
    entry_data = {"name": seq_name, "file_type": 1, "md5": md5,
                  "blast_hit_count": hit_count, "runtime": runtime,
                  "data": str({'file_data': "Data yo", "-num_iterations": "5"}),
                  }
    r = requests.post(entry_uri, data=entry_data)
    print(r.status_code)
    print(r.text)
else:
    # get blast file from cache
    pass