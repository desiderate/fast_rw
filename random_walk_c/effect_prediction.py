'''
Created on 2018. 10. 16.

@author: Gwangmin Kim
'''

import os
import sys
import time
import datetime
import smtplib
from email.mime.text import MIMEText
import psycopg2 as pg2

INIT_TIME = time.time()  # for pid
NOW = datetime.datetime.now()
NOW_DATE = NOW.strftime('%y%m%d')  # for pid


def ProcessingTime(startTime):
    endTime = time.time()
    print('## Processing Time:', str(datetime.timedelta(seconds=(endTime - startTime))))
    # startTime = time.time()
    # return startTime


def measure():
    global INIT_TIME
    after_time = time.time()
    dif_time = after_time - INIT_TIME
    hour = int(dif_time / 3660)
    mins = int((dif_time - hour * 3660) / 60)
    sec = dif_time - hour * 3660 - mins * 60
    print('\nStart Time: ' + NOW_DATE)
    print('Processing Time: ' + str(hour) + 'hour' + str(mins) + 'min' + str(sec) + 'sec')


def system_down_with_message(msg):
    print('\n#### ' + msg + '\n')
    sys.exit()


def coda_pgsql(sql):
    dictGene = {}
    conn = pg2.connect(database='coda3_0', user='sryim', host='heart5.kaist.ac.kr', password='bislaprom3')
    cur = conn.cursor()

    cur.execute(sql)
    query_output_list = cur.fetchall()

    return query_output_list


def coconut_pgsql(sql):
    conn = pg2.connect(host="heart4.kaist.ac.kr", user='full', password='zhzhsjt', database='COCONUTv2.1')
    curs = conn.cursor()  # Dictionary cursor
    curs.execute(sql)
    rows = curs.fetchall()
    conn.close()
    return rows


def get_pid(datetime=None):
    if datetime is None:
        return str(NOW_DATE)
    else:
        now_date_time = datetime.strftime('%y%m%d_%H:%M:%S_')  # for pid
        return str(now_date_time)


def send_email(email_list, process_id, msg_context):
    HOST = 'biosoft.kaist.ac.kr'
    smtp = smtplib.SMTP(HOST, 25)
    smtp.connect(HOST, 25)
    smtp.ehlo()
    smtp.starttls()
    smtp.login('gmkim@biosoft.kaist.ac.kr', 'tkzj2852')
    print("AUTH Success!")

    for email_address in email_list:
        msg = MIMEText(msg_context)
        msg['Subject'] = 'Analysis result for CODA'
        msg['To'] = email_address
        msg['From'] = 'coda@biosoft.kaist.ac.kr'

        smtp.sendmail('coda@biosoft.kaist.ac.kr', email_address, msg.as_string())
    smtp.quit()


def check_input_arguments(argument_list, built_in_parameter_dict, process_id):
    if len(argument_list) == 1:
        if argument_list[0] == '-h':
            msg = ''
            msg += "#" * 125 + '\n'
            msg += "[ HELP FOR 'randomwalk.py' ]\n"
            msg += '   python randomwalk.py [network_type] [input_type] [input1] [input2] ...\n'
            msg += "   - network_type: 'test' or 'level0' or 'level1'\n"
            msg += "   - input_type: 'herb' or 'compound' or 'gene'\n"
            msg += "   - input_list: What you want. If more than two, separate just space and cover each input with QUOTES\n"
            msg += "   - restart_rate: 0.7(defualt)\n"
            msg += " ex) python randomwalk.py test herb 'Panax ginseng' 'Xantium siribicum'\n"
            msg += " ex) python randomwalk.py level1 gene BRCA1 TNF MAPK1\n"
            msg += "#" * 125 + '\n'
            print(msg)
            sys.exit(0)

        elif argument_list[0] == '-i':
            msg = '\n[ BUILT-IN PARAMETERS ]\n'
            for parameter in built_in_parameter_dict.keys():
                msg += " - " + parameter + ": '" + built_in_parameter_dict[parameter] + "'\n"
            print(msg)
            sys.exit(0)

        else:
            system_down_with_message('Wrong input arguments, please try "python randomwalk.py -h"')

    elif len(argument_list) >= 3:
        network_type = argument_list[0]
        network = ''
        input_list = []

        # Check analysis type!
        if network_type.lower() == 'test' or network_type.lower() == 'level0' or network_type.lower() == 'level1':
            network = built_in_parameter_dict[network_type + "_network"]
            input_list = argument_list[2:]

        else:
            system_down_with_message('** Invalid network type, please set one of "test" or "level0" or "level1"!')

        # Check input type
        input_type = argument_list[1]
        if input_type.lower() == 'herb' or input_type.lower() == 'compound' or input_type.lower() == 'gene':
            pass
        else:
            system_down_with_message("Invalid input type, please set one of 'herb', 'compound' or 'gene'!")

        # Check built-in parameters
        result_directory = built_in_parameter_dict['result_directory']
        if not os.path.exists(result_directory):
            print("** '%s' directory does not exist, it automatically generate directory!" % result_directory)
            try:
                os.mkdir(result_directory, 511)

            except Exception as ex:
                system_down_with_message('It can not generate directory with error!\n\n%s' % str(ex))

        if os.path.exists(result_directory + '/' + process_id):
            system_down_with_message('Same process id exists, please try few seconds later!')

        else:
            try:
                os.mkdir(result_directory + '/' + process_id, 511)

            except Exception as ex:
                system_down_with_message('It can not generate directory with error!\n\n%s' % str(ex))

        return [network_type, network, input_type.lower(), input_list]

    else:
        system_down_with_message('Wrong input arguments, please try "python randomwalk.py -h"')


def randomwalk_with_restart(built_in_parameter_dict, input_arguments_list=sys.argv[1:]):
    # 0. INITIAL SETTING
    start_time = time.time()
    init_time = datetime.datetime.now().strftime('%y%m%d_%H_%M_%S_')
    process_id = init_time + '_' + '__'.join(input_arguments_list[2:]).replace(' ', '_')[:20]

    # 1. CHECK INPUT PARAMETERS, and ARGUMENTS
    network_type, network_file, input_type, input_list = check_input_arguments(input_arguments_list, built_in_parameter,
                                                                               process_id)
    print('\n** Process ID:', process_id)
    print('** INITIAL PARAMETER SETTING CHECKING IS FINISHED!\n')

    # 2. COCONUT DB Searching
    print("*** Start of S1_Herb_compound_gene.py")
    converted_input_list = []
    converted_input_list.append(input_type)

    for input in input_list:
        converted_input_list.append(input.replace(" ", "_"))
    print(converted_input_list)

    os.system(
        "python S1_Herb_compound_gene.py " + process_id + " " + network_type + " " + network_file + " " + " ".join(
            converted_input_list))

    # Pre-process for run RandomWalk.R
    # step2_time = time.time()
    # print("*** Start of S2_Make_DataSetForRandomWalk_mod.py")
    # os.system("python S2_Make_DataSetForRandomWalk_mod.py " + process_id + " " + network_type + " " + network_file + " " + 'seedGenes.txt')
    # ProcessingTime(step2_time)

    # Simulate RandomWalk Algorithm
    step3_time = time.time()
    print("***Start of S2_FastRandomWalk.py")
    os.system("python S2_FastRandomWalk.py " + process_id + ' ' + built_in_parameter_dict['restart_rate'] + " " +
              built_in_parameter_dict['random_walk_stop_threshold'])
    ProcessingTime(step3_time)

    # Calculate phenotypeRW_Score
    print("***Start of S3_Get_phenotype.py")
    os.system("python S3_Get_phenotype.py " + process_id)

    end_time = time.time()

    # Making Summary Output Page
    summary_output = open('results/%s/Summary.txt' % process_id, 'w+')
    summary_output.write("Molecule of interest\t" + '\t'.join(input_list) + '\n')
    summary_output.write("Networks\t" + str(network_file.split("/")[-1:]) + '\n')
    summary_output.write("Request date\t" + init_time + '\n')
    summary_output.write("Calculation time\t" + str(datetime.timedelta(seconds=(end_time - start_time))))
    summary_output.close()

    # Making dictionary-type outputs
    phenotype_dict = {}
    statistics_dict = {}
    summary_dict = {}
    phenotype_relation_dict = {}
    phenotype_clustering_dict = {}

    phenotype_output = open('results/%s/Phenotype_list.txt' % process_id, 'r')
    while True:
        phen_line = phenotype_output.readline()
        if not phen_line:
            break
        order, contents = phen_line.strip().split('\t', 1)
        phenotype_dict[order] = contents

    statistics_output = open('results/%s/Statistics.txt' % process_id, 'r')
    for stat_line in statistics_output.readlines():
        title, score_stat = stat_line.strip().split('\t')
        statistics_dict[title] = score_stat

    summary_dict["Molecule of interest"] = '\t'.join(input_list)
    summary_dict["Request date"] = init_time
    summary_dict["Calculation time"] = str(datetime.timedelta(seconds=(end_time - start_time)))

    phenotype_relation_output = open('results/%s/Phenotype_Relation_Matrix.txt' % process_id, 'r')
    index = 1
    for rel_line in phenotype_relation_output.readlines():
        left, right, score = rel_line.strip().split('\t')
        phenotype_relation_dict[index] = [left, right, score]
        index += 1
    phenotype_relation_output.close()

    # phenotype_clustering_output = open('results/%s/Clustered_phenotype.txt' % folder_name, 'r')
    # for clu_line in phenotype_clustering_output.readlines():
    #     representative_parent, children = clu_line.strip().split('\t')
    #     phenotype_clustering_dict[representative_parent] = children
    #     phenotype_clustering_output.close()

    print('## Whole Processing Time:', str(datetime.timedelta(seconds=(end_time - start_time))))
    return [phenotype_dict, statistics_dict, summary_dict, phenotype_relation_dict, phenotype_clustering_dict,
            process_id]


if __name__ == '__main__':
    built_in_parameter = {'test_network': 'network_files/light_network_level0.txt',
                          'level0_network': 'network_files/full_network_level0.txt',
                          'level1_network': 'network_files/full_network_level1.txt',
                          'restart_rate': '0.7',
                          'random_walk_stop_threshold': '0.0001',
                          'result_directory': 'results/'
                          }

    randomwalk_with_restart(built_in_parameter)
