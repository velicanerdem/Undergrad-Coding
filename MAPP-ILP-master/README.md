My solo graduation project at Sabanci University under Esra Erdem.

Summary: Under the ILP model given by Yu and La Valle (https://arxiv.org/abs/1507.03290) for Multi-Agent (may also be called Multi-Robot) Path Planning, this project implemented and analyzed the scalability / efficiency for Meeting problem (i.e. Given graph G, agents A within unique nodes in graph G, meeting locations / nodes as in M, find the shortest time in which agents can meet within one of m in M.) This was completed and further theoretical venues explored (Can ILP solve for problems such as Cargo Management?)   

Technical:
Requires Gurobi to be installed.

Python script for Gurobi solver (MRP_with_objectives_meeting_final) works if there is an existing gurobi installation in the computer.

In the folder:
	
1) gurobi_MRP texts:
	For each random example solved that has same variables, it stores the solve time.
	
2) read_file_total.py
	It reads each gurobi_MRP file to output means_e and std_e.
	
3) means_e and std_e
	means_e stores the mean of every example that has same variables, while std stores the standard deviation of them. Currently all numpy references are made comments.

Important: The transformation from Python script to text file is not optimized / hashed, it is advised that if the test / random mode would be run, the numbers should be small.
