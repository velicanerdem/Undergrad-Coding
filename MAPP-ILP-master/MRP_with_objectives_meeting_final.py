import random
import os
import time

start_cors_to_robots = dict()       #hash table for coordinates -> robots
start_robots_to_cors = dict()       #hash table for robots -> coordinates
meeting_places = set()              #meeting places for all robots to meet
obstacles = set()                   #vertices that can't be traversed (generated before graph is initialized, or after)
                                    #immovable objects (walls,pillars etc.)
graph = dict()                      #an abstraction allowing for direct translation of text file to a graph to solve
adjacency_set = dict()              #used for defining edges in a rectangular graph
edgeList = dict()                   
output = dict()                     #all ILP output in format .lp is stored here before writing to .lp file
robotEdges = set()
solution = dict()                   #read solutions from .sol file are stored here to be written
total_solve_time = 0
inaccessible_vertices = set()
constrained_vertices = dict()
output["vector_c"] = []
# inaccessible_vertices[r] = {v_1, v_2..} or {                                                                                                                                                                                                                                                                                                      }
#

#LP file usually takes a lot of space. If .lp file is not necessary it is advised to make this
delete_lp_file = True

length = 9
width = 9
robot = 30
colFrac = 0.3

meeting_p = 2
most_far_away = dict()

time_alg = length * width + length


#inaccessible_per_robot = length * width * 0.1
#inaccessible_robot = robot / 2

iteration_number = 20

user_mode = False
os_invokable = True


objectives = ["Normal", "MinDist", "MinTotalTime", "MinTotalDist"]
objective = "Normal"


def in_list_list(obj, list_list):
    for list in list_list:
        if obj in list:
            return True
    return False


def generate_inaccesible_vertices(number_per_robot, number_of_robots, *unwanted):
    global inaccessible_vertices

    for p in range(number_per_robot):
        for r in range(number_of_robots):
            x = random.randrange(width)
            y = random.randrange(length)
            cor = (y,x)
            while in_list_list(cor, unwanted) or (r,cor) in inaccessible_vertices():
                x = random.randrange(width)
                y = random.randrange(length)
                cor = (y,x)
            inaccessible_vertices.add(r, cor)

def generate_constrained_vertices(less_than_n, more_than_n, equal_to_n, *unwanted):
    global constrained_vertices

    for p in range(less_than_n):
        x = random.randrange(width)
        y = random.randrange(length)
        cor = (y,x)
        while in_list_list(cor, unwanted) or cor in constrained_vertices():
            x = random.randrange(width)
            y = random.randrange(length)
            cor = (y,x)
        x = random.randrange(robot)
        constrained_vertices[cor] = ("leq", x)

    for p in range(equal_to_n):
        x = random.randrange(width)
        y = random.randrange(length)
        cor = (y,x)
        while in_list_list(cor, unwanted) or cor in constrained_vertices():
            x = random.randrange(width)
            y = random.randrange(length)
            cor = (y,x)
        x = random.randrange(robot)
        constrained_vertices[cor] = ("eq", x)

    for p in range(more_than_n):
        x = random.randrange(width)
        y = random.randrange(length)
        cor = (y,x)
        while in_list_list(cor, unwanted) or cor in constrained_vertices():
            x = random.randrange(width)
            y = random.randrange(length)
            cor = (y,x)
        x = random.randrange(robot)
        constrained_vertices[cor] = ("geq", x)



def reinitialize_vars():

    global start_cors_to_robots
    global start_robots_to_cors
    global meeting_places
    global obstacles
    global graph
    global adjacency_set
    global edgeList
    global output
    global robotEdges
    global solution
    global most_far_away

    start_cors_to_robots = dict()
    start_robots_to_cors = dict()
    meeting_places = set()
    obstacles = set()

    graph = dict()
    adjacency_set = dict()
    edgeList = dict()
    output = dict()
    robotEdges = set()
    solution = dict()

    most_far_away = dict()


def create_neighbours(location):
    n = set()
    for x in [-1, 1]:
        for y in [-1, 1]:
            l = location[0][0] + x, location[0][1] + y
            l = l, location[1] + 1
            n.add(l)
        l = location[0][0] + x, location[0][1]
        l = l, location[1] + 1
        n.add(l)
    for y in [-1,1]:
        l = location[0][0], location[0][1] + y
        l = l, location[1] + 1
        n.add(l)
    return n


def expand_frontier(frontier, known, m_places):
    # Breadth first search
    global obstacles
    frontier_new = set(frontier)
    for f in frontier:
        known.add(f[0])
        for new in create_neighbours(f):
            if new[0] not in obstacles:
                if new[0] not in known:
                    if 0 <= new[0][0] < length and 0 <= new[0][1] < width:
                        if new[0] in m_places:
                            known.add(new[0])
                            if new[1] > most_far_away[new[0]]:
                                most_far_away[new[0]] = new[1]
                            m_places.remove(new[0])
                        else:
                            frontier_new.add(new)
        frontier_new.remove(f)

    return frontier_new


def reachable_graph():

    for r in range(robot):
        frontier = set()
        known = set()
        unreached_meeting_places = set(meeting_places)
        var_s = start_robots_to_cors[r], 0
        frontier.add(var_s)
        while len(frontier) != 0:
            frontier = expand_frontier(frontier, known, unreached_meeting_places)
            if len(unreached_meeting_places) == 0:
                break
        if len(frontier) == 0:
            return False

    return True


def generate_grid():
    global start_cors_to_robots
    global start_robots_to_cors
    global meeting_places
    global obstacles

    #viable map
    if int(length * width * (1 - colFrac)) <= robot-1:
        exit(-1)

    #generate obstacles: immovable objects
    for i in range(int(length * width * colFrac)):
        x = random.randrange(width)
        y = random.randrange(length)
        cor = (y,x)
        while cor in obstacles:
            x = random.randrange(width)
            y = random.randrange(length)
            cor = (y,x)
        obstacles.add(cor)

    #generate starting points
    for r in range(robot):
        x = random.randrange(width)
        y = random.randrange(length)
        loc = (y,x)
        while loc in start_cors_to_robots or loc in obstacles:
            #not same start, not collusion area
            x = random.randrange(width)
            y = random.randrange(length)
            loc = (y,x)
        start_cors_to_robots[loc] = r
        start_robots_to_cors[r] = loc

    #generate meeting points
    for r in range(meeting_p):
        #goal coordinates
        x = random.randrange(width)
        y = random.randrange(length)
        loc = (y,x)
        while loc in meeting_places or loc in obstacles or loc in start_cors_to_robots:
            x = random.randrange(width)
            y = random.randrange(length)
            loc = (y,x)
        meeting_places.add(loc)
        most_far_away[loc] = 0



    while not reachable_graph():
        reinitialize_vars()
        generate_grid()

    initialize_graph()


def generate_adjacency():
    for i in range(length):
        for j in range(width):
            loc = (i,j)
            if loc in obstacles:
                continue
            graph[loc] = dict()
            adjacency_set[loc] = []

            neighbour = [[0], [0]]
            if length -1 > i:
                neighbour[0].append(1)
            if i != 0:
                neighbour[0].append(-1)
            if width -1 > j:
                neighbour[1].append(1)
            if j != 0:
                neighbour[1].append(-1)
            for xit in neighbour[0]:
                for yit in neighbour[1]:
                    adj = i+xit,j+yit
                    if adj not in obstacles:
                        adjacency_set[loc].append(adj)


def initialize_graph():
    global graph

    generate_adjacency()

    for s in start_cors_to_robots:
        graph[s]["start"] = start_cors_to_robots[s]
    for g in meeting_places:
        graph[g]["meeting"] = True
    for loc in graph:
        if len(graph[loc]) == 0:
            graph[loc]["other"] = "empty"


def generate_objective(vector_out, vector_in, time):
    global output

    output["meeting_place"] = []
    output["meeting_place_sum"] = []
    if objective == "Normal":
        obj = ""
        # generate constraint so that robots can only go to one meeting place
        # can be done by forcing only one robot

        cons = "mp_0: "
        for m in meeting_places:
            var_first_robot = vector_out[m][time, 0][start_robots_to_cors[0]]
            cons += var_first_robot + " + "
            # make all loopback edges from a meeting place equivalent (to robot 0)
            inc = 1
            for r in range(1,robot):
                cons_eq = "mp_" + str(inc)
                inc += 1
                cons_eq += "_" + str(r) + ": "
                start_pos = start_robots_to_cors[r]
                var = vector_out[m][time,r][start_pos]
                cons_eq += var + " - " + var_first_robot + " = 0"
                output["meeting_place"].append(cons_eq)

        output["objective"] = ("max", cons[5:-2])
        cons = cons[:-2] + " = 1"
        output["meeting_place"].append(cons)
        


    if len(constrained_vertices) != 0:
        counter_l = 0
        counter_e = 0
        counter_g = 0

        for cor in constrained_vertices:
            if constrained_vertices[cor][0] == "leq":
                var_total = ""
                for r in range(robot):
                    var_name = "leq" + str(cor[0]) + "_" + str(cor[1]) + "_" + str(r)
                    output["variables"].append(var_name)
                    for t in range(time+1):
                        for loc in vector_in[cor][t,r]:
                            constraint = "clq" + str(++counter_l) + ": " +  var_name + " >= " + vector_in[cor][t,r][loc]
                            output["vector_c"].append(constraint)
                    var_total += var_name + " + "
                var_total = var_total[:-2]
                constraint = "leqv_" + str(cor[0]) + "_" + str(cor[1]) + ": " + var_total + " < " \
                             + str(constrained_vertices[cor][1])
                output["vector_c"].append(constraint)

            if constrained_vertices[cor][0] == "eq":
                con_total = ""
                for r in range(robot):
                    var_total = ""
                    var_name = "eq" + str(cor[0]) + "_" + str(cor[1]) + "_" + str(r)
                    output["variables"].append(var_name)
                    con_total += var_name + " + "
                    constraint_n = "ceq" + str(++counter_e) + ": " +  var_name + " <= "
                    for t in range(time+1):
                        for loc in vector_in[cor][t,r]:
                            var_total += vector_in[cor][t,r][loc] + " + "
                    var_total = var_total[:-2]
                    constraint_n += var_total
                    output["vector_c"].append(constraint)
                con_total = con_total[:-2]
                cons = "eqv_" + str(cor[0]) + "_" + str(cor[1]) + ": " + con_total + " = "\
                       + str(constrained_vertices[cor][1])
                output["vector_c"].append(cons)

            if constrained_vertices[cor][0] == "eq":
                con_total = ""
                for r in range(robot):
                    var_total = ""
                    var_name = "geq" + str(cor[0]) + "_" + str(cor[1]) + "_" + str(r)
                    output["variables"].append(var_name)
                    con_total += var_name + " + "
                    constraint_n = "cgq" + str(++counter_g) + ": " +  var_name + " <= "
                    for t in range(time+1):
                        for loc in vector_in[cor][t,r]:
                            var_total += vector_in[cor][t,r][loc] + " + "
                    var_total = var_total[:-2]
                    constraint_n += var_total
                    output["vector_c"].append(constraint)
                con_total = con_total[:-2]
                cons = "gqv_" + str(cor[0]) + "_" + str(cor[1]) + ": " + con_total + " => "\
                       + str(constrained_vertices[cor][1])
                output["vector_c"].append(cons)






    # var_objective = "obj_const"
    # cons_start = "rc"
    #
    # output["cons_obj"] = {}

    # if objective == "MinDist":
    #     for r in range(robot):
    #         obj_rob_const = ""
    #         cons_robot = cons_start + str(r) + ": "
    #         for t in range(time):
    #             for loc1 in graph:
    #                 for loc2 in graph:
    #                     if loc1 != loc2:
    #                         obj_rob_const += vector_out[loc1][t,r][loc2] + " + "
    #         obj_rob_const = obj_rob_const[:-3]
    #         output["cons_obj"].add(cons_robot + var_objective + " > " + obj_rob_const)
    #     output["objective"] = ("min", var_objective)
    #
    # if objective == "MinTotalTime":
    #     for r in range(robot):
    #         obj_rob_const = ""
    #         goal_pos = start_robots_to_cors[r]
    #         cons_robot = cons_start + str(r) + ": "
    #         output["variables"].append(cons_robot)
    #         for t in range(time):
    #             if t != time-1:
    #                 obj_rob_const += vector_out[goal_pos][t,r][goal_pos] + " + "
    #         output["cons_obj"].add(cons_robot + var_objective + " < " + obj_rob_const)
    #     output["objective"] = ("max", var_objective)
    #     return


def generate_constraints(time):
    global output

    counter = 1
    vector_in = dict()
    vector_out = dict()

    for loc in graph:
        vector_in[loc] = {}
        vector_out[loc] = {}
        for t in range(time+1):
            for r in range(robot):
                vector_in[loc][t,r] = {}
                vector_out[loc][t,r] = {}

    output["variables"] = list()
    #edge constaint start
    if time > 0:
        for r in range(robot):
            startloc = start_robots_to_cors[r]
            for adj in adjacency_set[startloc]:
                varname = "e_" + str(startloc[0]) + "_" + str(startloc[1]) + "__n"
                varname += str(adj[0]) + "_" + str(adj[1]) + "_T0"
                varname += "_R" + str(r)
                output["variables"].append(varname)
                vector_in[adj][0,r][startloc] = varname
                vector_out[startloc][0,r][adj] = varname

    # edge constraint normal
    for loc in graph:
        for adj in adjacency_set[loc]:
            varname = "e_" + str(loc[0]) + "_" + str(loc[1]) + "__n" + str(adj[0]) + "_" + str(adj[1])
            for t in range(time):
                vartime = varname + "_T" + str(t) + "_"
                for r in range(robot):
                    var = vartime + "R" + str(r)
                    output["variables"].append(var)

                    # example: "e1_20_13__12_e2_25_R4_T12: <= 1"
                    # output["normal_edges"][t].append(constraint)

                    if loc not in meeting_places or adj == loc:
                        vector_out[loc][t,r][adj] = var
                    vector_in[adj][t,r][loc] = var

    # edge constraint loopback
    var = "LB_"
    output["LB_edges"] = []
    obj = ""

    for r in range(robot):
        startloc = start_robots_to_cors[r]
        for m in meeting_places:
            var = "LB_" + str(m[0]) + "_" + str(m[1]) + "__" + str(startloc[0]) + "_" + str(startloc[1])
            var = var + "_T" + str(time) + "_R" + str(r)
            output["variables"].append(var)
            vector_out[m][time, r][startloc] = var
            vector_in[startloc][time, r][m] = var

    # specific for each robot
    # nonterminal
    output["flowEq"] = []
    for loc in graph:
        for t in range(time):
            for r in range(robot):
                consname = "flowEq" + str(counter) + ": "
                counter += 1
                var_in = ""
                var_out= ""
                for inEdge in vector_in[loc][t,r]:
                    var_in += vector_in[loc][t,r][inEdge] + " + "

                for outEdge in vector_out[loc][t+1,r]:
                    var_out += vector_out[loc][t+1,r][outEdge] + " - "

                if var_in != "":
                    if var_out != "":
                        var_in = var_in[:-2]
                        var_out = var_out[:-2]
                        constraint = consname + var_in + " - " + var_out + " = 0"
                        output["flowEq"].append(constraint)
                    else:
                        var_in = var_in[:-2]
                        constraint = consname + var_in + " = 0"
                        output["flowEq"].append(constraint)
                else:
                    if var_out != "":
                        var_out = var_out[:-2]
                        constraint = consname + var_out + "= 0"
                        output["flowEq"].append(constraint)

    # terminal

    const = "flowEq_end"
    for r in range(robot):
        consname = const + "_r" + str(r) + ": "
        startloc = start_robots_to_cors[r]
        var_out = ""
        var_in = ""
        for outEdge in vector_out[startloc][0,r]:
            var_out += vector_out[startloc][0,r][outEdge] + " + "
        for m in meeting_places:
            var_in += vector_in[startloc][time,r][m] + " - "
        if var_out != "":
            var_out = var_out[:-3]
            var_in = var_in[:-3]
            constraint = consname + var_out + " - " + var_in + " = 0"
            output["flowEq"].append(constraint)
        else:
            var_in = var_in[:-3]
            constraint = consname + var_in + " = 0"
            output["flowEq"].append(constraint)

    output["vertex_in"] = list()
    output["vertex_out"] = list()

    # to make sure only 1 robot can get in and get out
    # vertex_out is unnecessary when vertex_in is constrained
    for loc in graph:
        if loc in meeting_places or loc in obstacles:
            continue
        for t in range(time+1):
            var_in = ""
            var_out = ""
            consname = "vertex" + str(counter)
            counter += 1
            for r in range(robot):
                for inEdge in vector_in[loc][t,r]:
                    var_in += vector_in[loc][t,r][inEdge] + " + "
                for outEdge in vector_out[loc][t,r]:
                    var_out += vector_out[loc][t,r][outEdge] + " + "

            if len(var_in) > 2:
                var_in = var_in[:-3]
                var_in = var_in
                constraint_in = consname + "_in" + ": " + var_in  + " <= 1"
                output["vertex_in"].append(constraint_in)
            if len(var_out) > 2:
                var_out = var_out[:-3]
                constraint_out = consname + "_out" + ": " + var_out + " <= 1"
                output["vertex_out"].append(constraint_out)

    output["col_check"] = list()

    for loc in graph:
        if loc not in obstacles and loc not in meeting_places:
            for adj in adjacency_set[loc]:
                if adj not in meeting_places and loc > adj:
                    consname = "colcheck_" + str(loc[0]) + str(loc[1]) + "_" + str(adj[0]) + str(adj[1]) + "_"
                    consname += str(counter) + "_"
                    counter += 1
                    for t in range(1,time):
                        constime = consname + "T" + str(t) + "_"
                        for locr in range(robot):
                            for adjr in range(robot):
                                if locr != adjr:    #floweq provides that robots cant be equal
                                    varLoc = vector_out[loc][t,locr][adj]
                                    varAdj = vector_out[adj][t,adjr][loc]
                                    consrobot = "R" + str(locr) + "_R" + str(adjr) + ":"
                                    constraint = constime + consrobot + "  " + varLoc + " + " + varAdj + " <= 1"

                                    output["col_check"].append(constraint)
    if time > 0:
        for r in range(robot):
            startloc = start_robots_to_cors[r]
            for adj in adjacency_set[startloc]:
                if adj in start_cors_to_robots:
                    if startloc > adj:
                        consname = "cols_check_" + str(startloc[0]) + str(startloc[1]) + "_" + str(adj[0]) + str(adj[1]) + "_"
                        constime = consname + "T0_"
                        r_adj = start_cors_to_robots[adj]
                        var_adjout = vector_out[adj][0,r_adj][startloc]
                        var_locout = vector_out[startloc][0,r][adj]
                        consrobot = "R" + str(r) + "_R" + str(r_adj) + ":"
                        constraint = constime + consrobot + "  " + var_locout + " + " + var_adjout + " <= 1"
                        output["col_check"].append(constraint)

    generate_objective(vector_out, vector_in, time)


def read_graph_from_file(start_name, goal_name):
    global length
    global width
    global colFrac
    global start_cors_to_robots
    global meeting_places
    global obstacles
    global graph
    global adjacency_set
    global robot
    global meeting_p
    start_file = open(start_name)
    goal_file = open(goal_name)

    start_row = start_file.readlines()

    length = len(start_row)

    robot = 0
    meeting_p = 0
    for r in range(length):
        row = start_row[r]
        row_split = row.rsplit(" ")
        for i in range(len(row_split)):
            if row_split[i].startswith("S"):
                robot_id = row_split[i][1:]
                start_cors_to_robots[i] = robot_id
                start_robots_to_cors[robot_id] = int(r),int(i)
                ++robot
            if row_split[i].startswith("G"):
                meeting_places.add(int(r),int(i))
                ++meeting_p


    initialize_graph()

def write_graph_to_file(filename):
    global graph
    graphfilestart = open(filename + '_start.txt', "w")

    graphoutputStart = []

    for l in range(length):
        graphoutputStart.append([])
        for w in range(width):
            graphoutputStart[l].append("XX ")

    for loc in graph:
        if "other" in graph[loc]:
            if graph[loc]["other"] == "empty":
                graphoutputStart[loc[0]][loc[1]] = "-- "
        else:
            graphoutputStart[loc[0]][loc[1]] = "-- "
            if "start" in graph[loc]:
                graphoutputStart[loc[0]][loc[1]] = "S" + str(graph[loc]["start"]) + " "
            if "meeting" in graph[loc]:
                graphoutputStart[loc[0]][loc[1]] = "G  "

    for l in range(length):
        for w in range(width):
            graphfilestart.write(graphoutputStart[l][w])

        graphfilestart.write("\n")

    graphfilestart.close()


def write_constraints(filename):
    global output
    f = open(filename, 'w')
    obj = output["objective"][1]
    if output["objective"][0] == "max":
        f.write("Maximize\n")
    else:
        f.write("Minimize\n")
    f.write("  ")
    f.write(obj + "\n")
    f.write("Subject to\n")
    # for t in range(time):
    #    for cons in output["normal_edges"][t]:
    #        f.write("  " + cons + "\n")

    for i in output["meeting_place"]:
        f.write("  " + i + "\n")

    for i in output["LB_edges"]:
        f.write("  " + i + "\n")
    for i in output["flowEq"]:
        f.write("  " + i + "\n")

    for v in output["vertex_in"]:
        f.write("  " + v + "\n")
    for v in output["vertex_out"]:
        f.write("  " + v + "\n")
    for c in output["col_check"]:
        f.write("  " + c + "\n")
    # for o in output["obj_cons"]:
    #     f.write("  " + o + "\n")


    f.write("Lazy Constraints\n")
    for i in output["meeting_place_sum"]:
        f.write("  " + i + "\n")

    f.write("Binary\n")
    f.write("  ")
    for e in output["variables"]:
        f.write(e + "\t")

    f.write("\nEnd")
    f.close()


def get_user_input():
    print("Please select an option:")
    print("1: read graph from file")
    print("2: generate a random graph")

    selection = input()
    accepted_answers = [1,2]
    while selection not in accepted_answers:
        print("Please write either 1 or 2")
        selection = input()
    return selection


def read_solution(solpath):
    global solution
    f = open(solpath, 'r')
#   get rid of first line
    f.readline()
#   all variables and their values
    var_list = f.readlines()
    for var in var_list:
        if var.startswith('e'):
                if var.endswith('1\n'):

                    xt = var.find('T')
                    yt = var.find('_', xt)
                    t = int(var[xt+1:yt])

                    xr = var.find('R')
                    yr = var.find(' ', xr)
                    r = int(var[xr+1:yr])

                    xl = var.find("n")
                    yl = var.find("_", xl)
                    l = int(var[xl+1:yl])

                    xw = yl + 1
                    yw = var.find("_", xw)
                    w = int(var[xw:yw])

                    solution[t,r] = int(l),int(w)


def write_solution(path_new, time_comp):
    global obstacles
    global solution
    filename = path_new + "/position_t"
    for t in range(time_comp):
        #initialize output
        f = open(filename + str(t+1) + ".txt", 'w')
        graph_output = []
        for i in range(length):
            graph_output.append([])
            for j in range(width):
                graph_output[i].append("-- ")
        for cor in obstacles:
            graph_output[cor[0]][cor[1]] = "XX "
        for r in range(robot):
            loc = solution[t,r]
            graph_output[loc[0]][loc[1]] = "R" + str(r) + " "
        for line in graph_output:
            for ins in line:
                f.write(ins)
            f.write('\n')
        f.close()
    return

def write_time_file(file_name, t):
    f = open(file_name, 'a')
    f.write(str(t) + "\n")
    f.close()

def solve_MRP():

    global length
    global width
    global colFrac
    global start_cors_to_robots
    global meeting_places
    global obstacles
    global graph
    global adjacency_set
    global time_alg
    global edgeList
    global output
    global robotEdges
    global solution
    global meeting_p
    global total_solve_time

    id = "gurobi_MRP_L" + str(length) + "_W" + str(width) + "_R" + str(robot) + "_C" + str(colFrac) + "_M" + str(meeting_p)
    cwd = os.getcwd()
    path = cwd + "/gurobi_MRP_veli"            #my name so it won't mess up with anything on a computer
    if not os.path.exists(path):
        os.mkdir(path)
    counter = 0
    path_n = path + "/" + id + "_u"
    path_new = path_n + str(counter)
    while os.path.exists(path_new):
        counter += 1
        path_new = path_n + str(counter)
    os.mkdir(path_new)
    write_graph_to_file(path_new + "/" + "gurobi_MRP")

    for t in range(min(most_far_away.values()), time_alg+1):
        generate_constraints(t)
        filename = path_new + '/gurobi_MRP_' + str(t) + ".lp"
        write_constraints(filename)
        solpath =  path_new + "/model.sol"
        if os_invokable:
            begin_time = time.time()
            os.system("gurobi_cl Result_File=" + solpath + " " + filename) #">" + path_new + "/g.log"
            total_time = time.time() - begin_time
            total_solve_time += total_time
            if os.path.getsize(solpath) > 0:    #solution exits
                #os.path.exists(solpath) and
                read_solution(solpath)
                write_solution(path_new, t)
                if delete_lp_file:
                    os.remove(filename)
                write_time_file(path + "/" + id + ".mrp", total_time)
                break
            else:
                os.remove(filename)
                if t == time_alg:
                    print("Not solvable")
                    exit()
    if not os_invokable:
        print("Press a key when problem has been solved")
        print("Make sure model.sol is in the same directory as .log")
        input()
        read_solution(solpath)
        write_solution(path_new, t)

if user_mode:
    print("To input a graph into algorithm, enter 1. To generate a graph from variables and solve it, enter 2")
    selection = get_user_input()
    if selection == 1:
        print("Please enter the path that graph file is in")
        path = input()
        if not path.endswith("/"):
            path += "/"
        print("Enter the graph start file name")
        start_name = path + input()
        print("Enter the graph goal file name")
        goal_name = path + input()

        read_graph_from_file(start_name, goal_name)
        solve_MRP()

    if selection == 2:
        print("Enter time")
        time_alg = input()
        print("Enter length of the graph")
        length = input()
        print("Enter width of the graph")
        width = input()
        print("Enter robot number")
        robot = input()
        print("Enter collusion fraction with '.'")
        colFrac = input()
        print("Enter the number of meeting places")
        meeting_p = input()
        generate_grid()

    solve_MRP()

else:
   for i in range(iteration_number):
        generate_grid()
        solve_MRP()
        reinitialize_vars()