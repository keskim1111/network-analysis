import networkx as nx
import struct

from consts import yeast_com, yeast_edges, edge_file
from evaluation import jaccard, graph_accuracy, graph_sensitivity, modularity
from input_networks import create_graph_from_edge_list, create_graph_from_edge_list_strings, read_communities_file, create_random_network
from output_generator import write_to_file
from helpers import timeit, current_time


def createMapping(edge_file):
    d = dict()
    G = create_graph_from_edge_list(edge_file)
    i = 0
    nodes = sorted(G.nodes)
    for node in nodes:
        d[i] = node
        i+=1
    return d

@timeit
def read_binary_network_input(fileName, edgesFile=None):
    """
    :param: fileName of a binary file of the following format:
            The first value represents the number of nodes in the network, n = |V |.
            The second value represents the number of edges of the first node, i.e., k1. It is followed by
            the k1 indices of its neighbors, in increasing order.
            The next value is k2, followed by the k2 indices of the neighbors of the second node, then k3
            and its k3 neighbors, and so on until node n.
    :return: a networkX graph created based on the binary file
    """
    G = nx.Graph()
    f = open(fileName, "rb")
    try:
        if (edgesFile != None):
            mapping = createMapping(edgesFile)
        num_of_nodes_byte = f.read(4)
        num_of_nodes = struct.unpack('i', num_of_nodes_byte)[0]
        # print(f"num_of_nodes {num_of_nodes}")
        for i in range(num_of_nodes):
            if edgesFile != None:
                node = mapping[i]
            else:
                node = i
            num_of_neighbors_byte = f.read(4)
            num_of_neighbors = struct.unpack('i', num_of_neighbors_byte)[0]
            # print(f"*num_of_neighbors of {i} is {num_of_neighbors}")
            for j in range(num_of_neighbors):
                neighbor_byte = f.read(4)
                neighbor = struct.unpack('i', neighbor_byte)[0]
                G.add_edge(node, neighbor)
            # print(f"num_of_neighbors of {i} is {len([n for n in G.neighbors(i)])}")
    finally:
        f.close()
    return G

@timeit
def read_binary_network_output(fileName):
    """
    :param: fileName of a binary file of the following format:
            The first value represents the number of nodes in the network, n = |V |.
            The second value represents the number of edges of the first node, i.e., k1. It is followed by
            the k1 indices of its neighbors, in increasing order.
            The next value is k2, followed by the k2 indices of the neighbors of the second node, then k3
            and its k3 neighbors, and so on until node n.
    :return: a networkX graph created based on the binary file
    """
    f = open(fileName, "rb")
    res = []
    try:
        num_of_groups_byte = f.read(4)
        num_of_groups = struct.unpack('i', num_of_groups_byte)[0]
        for i in range(num_of_groups):
            group = []
            num_of_nodes_in_group_byte = f.read(4)
            num_of_nodes_in_group = struct.unpack('i', num_of_nodes_in_group_byte)[0]
            for j in range(num_of_nodes_in_group):
                group_member_byte = f.read(4)
                group_member = struct.unpack('i', group_member_byte)[0]
                group.append(group_member)
            res.append(group)
    finally:
        f.close()
    return res



def create_binary_network_file(G):
    """
    :param: G - a networkX graph created based on the binary file
    :return: A path to a binary file created in the following format:
            The first value represents the number of nodes in the network, n = |V |.
            The second value represents the number of edges of the first node, i.e., k1. It is followed by
            the k1 indices of its neighbors, in increasing order.
            The next value is k2, followed by the k2 indices of the neighbors of the second node, then k3
            and its k3 neighbors, and so on until node n.
    """
    file_name = f'{current_time()}-graph.in'
    f = open(file_name, "wb")
    try:
        nodes_list = sorted(G.nodes())
        num_of_nodes = len(nodes_list)
        f.write(struct.pack('i', num_of_nodes))
        for node in nodes_list:
            neighbors = sorted(list(G.neighbors(node)))
            num_of_neighbors = len(neighbors)
            f.write(struct.pack('i', num_of_neighbors))
            for neighbor in neighbors:
                f.write(struct.pack('i', int(neighbor)))
    finally:
        f.close()
    print(file_name)
    return file_name

# TODO remove after
def create_for_esty_from_edges_strings(edge_list):
    print(f"The path is {edge_list}")
    G = create_graph_from_edge_list_strings(edge_list)
    print(G)
    return create_binary_network_file(G)

def create_for_esty_from_edges(edge_list):
    print(f"The path is {edge_list}")
    G = create_graph_from_edge_list(edge_list)
    return create_binary_network_file(G)

def compare_c_output_to_real(output_path, real_communities_path, real_edges_path ):
    our_communities = read_binary_network_output(output_path)
    G = read_binary_network_input(real_edges_path)
    # real_communities = read_communities_file(real_communities_path)
    real_communities = real_communities_path
    # G = create_graph_from_edge_list(real_edges_path)
    print("###### Results ##########")
    print(f"num of our communities is: {len(our_communities)}")
    print(f"min size of a community (from ours): {min([len(group) for group in our_communities])}")
    print(f"max size of a community (from ours): {max([len(group) for group in our_communities])}")
    print(our_communities)
    print(f"num of  real communities is: {len(real_communities)}")
    print(real_communities)
    print("modularity is")
    print(modularity(G, our_communities))
    print("jaccard is")
    print(jaccard(our_communities, real_communities))
    print("graph_sensitivity is")
    print(graph_sensitivity(real_communities, our_communities))
    print("graph_accuracy is")
    print(graph_accuracy(real_communities, our_communities))
    Differences = [list(j) for j in {tuple(i) for i in real_communities} ^ {tuple(i) for i in our_communities}]
    print(f"diff is {Differences}")
real = [[645, 903, 265, 526, 783, 916, 662, 22, 536, 214, 96, 248, 98, 37, 42, 45, 119, 824, 121, 316, 895], [257, 401, 531, 541, 161, 931, 420, 810, 299, 428, 171, 170, 427, 556, 47, 176, 948, 437, 564, 956, 445, 573, 703, 960, 958, 60, 323, 195, 325, 454, 63, 968, 715, 75, 718, 719, 594, 342, 856, 344, 857, 89, 992, 993, 482, 229, 742, 613, 360, 362, 107, 110, 239, 115, 379, 508], [273, 785, 21, 282, 794, 540, 31, 801, 550, 806, 814, 818, 562, 828, 829, 61, 65, 322, 835, 836, 580, 327, 840, 73, 842, 588, 339, 597, 346, 606, 866, 101, 877, 367, 368, 113, 117, 633, 635, 382, 140, 145, 913, 918, 666, 157, 927, 431, 690, 438, 695, 182, 702, 706, 969, 203, 204, 462, 975, 211, 981, 996, 741, 747, 507, 511], [256, 384, 514, 897, 137, 779, 523, 907, 17, 149, 923, 34, 418, 548, 38, 39, 49, 817, 433, 947, 952, 697, 324, 455, 201, 208, 721, 217, 735, 609, 97, 611, 126, 485, 617, 489, 365, 750, 623, 751, 242, 243, 254, 378, 510, 255], [449, 258, 131, 132, 389, 70, 653, 910, 14, 81, 532, 277, 533, 279, 535, 795, 284, 158, 287, 160, 869, 294, 614, 745, 558, 441, 315, 125], [0, 576, 196, 200, 525, 979, 983, 734, 616, 490, 363, 940, 51, 501, 54, 247, 953, 636, 189, 319], [3, 518, 904, 393, 136, 651, 395, 15, 656, 914, 786, 660, 276, 406, 408, 154, 414, 289, 419, 165, 934, 422, 551, 937, 553, 555, 300, 46, 816, 435, 821, 53, 567, 313, 954, 59, 955, 574, 830, 834, 837, 967, 711, 329, 724, 469, 91, 476, 353, 102, 487, 359, 496, 883, 755, 629, 246, 120, 377, 122], [267, 780, 787, 283, 800, 809, 811, 813, 820, 58, 320, 586, 843, 589, 78, 846, 858, 356, 357, 615, 871, 872, 875, 371, 118, 391, 655, 402, 919, 667, 925, 926, 671, 672, 932, 678, 680, 425, 172, 173, 436, 442, 443, 959, 448, 962, 450, 709, 197, 453, 456, 457, 972, 210, 213, 726, 474, 732, 478, 991, 738, 997, 743, 999, 752, 754], [129, 901, 262, 133, 650, 909, 270, 143, 417, 33, 546, 293, 48, 560, 946, 949, 568, 583, 970, 716, 335, 337, 341, 473, 602, 348, 349, 221, 483, 358, 618, 876, 885, 374, 506, 892], [128, 512, 516, 5, 646, 7, 264, 776, 266, 268, 398, 272, 147, 25, 155, 929, 291, 552, 43, 429, 575, 193, 841, 205, 759, 620, 621, 878, 622, 749, 112, 111, 494, 886, 503, 891, 381], [8, 274, 788, 280, 792, 288, 298, 305, 308, 565, 566, 56, 825, 62, 64, 833, 578, 582, 839, 72, 585, 328, 77, 850, 84, 599, 855, 352, 99, 879, 369, 627, 639, 648, 906, 399, 148, 150, 663, 670, 159, 416, 676, 936, 681, 939, 174, 175, 945, 696, 187, 192, 704, 708, 971, 460, 717, 461, 974, 978, 466, 472, 220, 481, 994, 739, 484, 235], [579, 900, 261, 517, 647, 392, 587, 396, 332, 76, 784, 657, 275, 83, 278, 26, 924, 285, 413, 543, 29, 605, 862, 104, 41, 44, 686, 559, 500, 571, 446], [385, 130, 515, 772, 775, 520, 11, 397, 912, 404, 793, 281, 35, 554, 563, 185, 963, 965, 326, 973, 207, 720, 209, 596, 982, 477, 94, 479, 480, 865, 631, 746, 491, 492, 106, 632, 624, 241, 370, 114, 375, 760, 250, 765], [768, 4, 652, 665, 668, 797, 286, 799, 544, 32, 802, 805, 549, 933, 808, 169, 426, 812, 302, 942, 432, 688, 50, 694, 184, 699, 317, 447, 451, 581, 838, 330, 714, 206, 849, 722, 468, 87, 88, 727, 984, 215, 471, 861, 219, 95, 225, 355, 612, 995, 870, 486, 488, 105, 493, 240, 499, 887, 888, 252, 893, 766], [640, 386, 643, 899, 771, 644, 263, 774, 905, 521, 394, 141, 528, 789, 23, 153, 30, 928, 162, 166, 40, 301, 52, 440, 69, 71, 333, 361, 884, 373, 505, 637, 127], [513, 778, 524, 782, 16, 529, 530, 18, 20, 534, 791, 538, 539, 28, 542, 545, 290, 547, 36, 803, 296, 303, 306, 819, 823, 311, 57, 569, 570, 826, 314, 832, 66, 844, 79, 848, 82, 595, 343, 93, 863, 354, 867, 625, 882, 372, 634, 124, 638, 383, 641, 388, 902, 138, 139, 911, 400, 917, 151, 921, 412, 415, 930, 163, 423, 168, 683, 684, 180, 186, 194, 707, 452, 459, 977, 216, 729, 985, 731, 988, 222, 224, 744, 748, 238, 758, 761, 763, 509], [1, 390, 13, 271, 403, 790, 537, 675, 164, 677, 421, 807, 679, 938, 682, 685, 943, 693, 310, 312, 698, 572, 700, 318, 957, 321, 705, 67, 964, 710, 198, 584, 334, 847, 336, 465, 340, 853, 86, 212, 608, 740, 998, 236, 881, 756, 244, 502, 757, 504, 890, 251, 380, 767], [896, 769, 642, 387, 199, 777, 649, 74, 55, 85, 409, 796, 228, 108, 495, 944, 689, 178, 177, 116, 309, 181, 183, 827, 188, 191], [259, 522, 12, 527, 19, 407, 24, 922, 27, 411, 561, 951, 701, 68, 202, 331, 845, 976, 592, 338, 851, 852, 723, 854, 730, 859, 860, 989, 350, 351, 736, 92, 868, 100, 231, 873, 874, 234, 619, 366, 376], [2, 770, 260, 6, 9, 10, 781, 269, 292, 295, 297, 815, 307, 831, 577, 590, 591, 80, 593, 598, 600, 601, 603, 347, 607, 109, 628, 630, 894, 898, 135, 908, 654, 142, 658, 659, 915, 661, 405, 664, 152, 920, 410, 156, 669, 935, 424, 941, 430, 687, 434, 179, 692, 950, 439, 444, 190, 966, 712, 713, 458, 463, 464, 467, 980, 725, 470, 728, 218, 987, 475, 733, 223, 227, 230, 232, 237, 497, 253], [773, 134, 519, 144, 146, 798, 673, 674, 804, 167, 557, 304, 691, 822, 961, 345, 986, 90, 604, 990, 889, 864, 737, 610, 226, 103, 233, 364, 880, 753, 498, 626, 245, 249, 762, 123, 764]]

def check_edges():
    G = create_graph_from_edge_list(edge_file)
    path = create_binary_network_file(G)
    G2 = read_binary_network_input(path,edge_file)
    assert are_graphs_the_same(G, G2)

def check_lfr():
    n = 250
    mu = 0.1
    tau1 = 3
    tau2 = 1.5
    average_degree = 5
    min_com = 20
    G = create_random_network(n, mu, tau1, tau2, average_degree, min_com)
    path = create_binary_network_file(G)
    G2 = read_binary_network_input(path)
    assert are_graphs_the_same(G, G2)

def are_graphs_the_same(G, H):
    R = nx.difference(G, H)
    return len(R.edges) == 0


if __name__ == '__main__':
    pass


