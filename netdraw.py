# -*- coding: utf-8 -*-

'''
Created on 2017年11月15日

@author: azl
'''

import sys
import re

import networkx as nx
import matplotlib.pyplot as plt

import getopt


def split_edge_str(edge_str):
    edge_str = edge_str.strip()
    # print(re.split('[\s]*,?[,\s]*', edge_str))
    return (tuple(int(i) for i in re.split('[\s]*,?[\s]*', edge_str)))


def edges_list_file(file_name):
    """ 从文件中读取边数据
    Parameters
    ----------
    file_name : string 包含数据的文件名            
    """    
    edges_list = []
    with open(file_name) as f:
        try:
            for edge_str in f:
                edges_list.append(split_edge_str(edge_str))
        except(ValueError):
            print(u'\n输入数据格式错误\n')
            sys.exit()
            
    return edges_list           


def edges_list_stdin():
    """ 从标准输入读取边数据  """
    
    print(u'''
    请输入 n行，每行表示一条边的两个顶点  ： x y
    ''')    
    edges_list = []
    try:
        while True:
            edge_str = raw_input('\t')
            edges_list.append(split_edge_str(edge_str))
    except(EOFError, KeyboardInterrupt):
        print(u'\n输入结束\n')
    except(ValueError):
        print(u'\n输入数据格式错误\n')
        sys.exit()

    return edges_list


def print_graph_info(G):
    """ 打印图的信息包括点的数目，边的数量 """
    print(u'Total Nodes %d'%len(G.nodes()))
    print(u'Total Edges %d'%len(G.edges()))


def create_graph(edges_list):
    return nx.Graph(edges_list)


def draw_graph(G):
    nx.draw(G, labels={k: 'Node: %d\nDegree: %d'%(k, v) for k, v in G.degree()}, style="dashdot")
    plt.show()


def save_garph(G, filename):
    nx.draw(G, labels={k: 'Node: %d\nDegree: %d'%(k, v) for k, v in G.degree()}, style="dashdot")
    plt.savefig(fname=filename)       


def print_usage():
    print(u'''
    Usage: netdraw.py [options]
    options:
        -o filename 图像输出路径
        -f filename 输入文件路径
    ''')

if __name__ == '__main__':
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'o:f:', [])
    except getopt.GetoptError:
        print_usage()
        sys.exit()
     
    edges_list = None
    output_file = None   
    for opt_name, opt_value in opts:
        if opt_name in ('-f'):
            edges_list = edges_list_file(opt_value)
        elif opt_name in ('-o'):
            output_file = opt_value

    if edges_list is None:
        edges_list = edges_list_stdin()
        
    G = create_graph(edges_list)
    
    print_graph_info(G)    

    if output_file is not None: save_garph(G, output_file)    
    else: draw_graph(G)


    
