#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#include "graphio.h"
#include "graph.h"


//#define FRONTIER_NUM = 256
#define LARGE_NUM 99999

#define NOT_TRAVERSED 1
#define TRAVERSED 0
#ifndef OMP_NUM_THREADS
    #define OMP_NUM_THREADS 64
#endif

char gfile[2048];

void usage(){
  printf("./bfs <filename> <sourceIndex>\n");
  exit(0);
}


/*
  You can ignore the ewgths and vwghts. They are there as the read function expects those values
  row_ptr and col_ind are the CRS entities. nov is the Number of Vertices
*/
int main(int argc, char *argv[]) {
  etype *row_ptr;
  vtype *col_ind;
  ewtype *ewghts;
  vwtype *vwghts;
  vtype nov, source;

  if(argc != 3)
    usage();

  const char* fname = argv[1];
  strcpy(gfile, fname);
  source = atoi(argv[2]);
  
  if(read_graph(gfile, &row_ptr, &col_ind, &ewghts, &vwghts, &nov, 0) == -1) {
    printf("error in graph read\n");
    exit(1);
  }
  
  /****** YOUR CODE GOES HERE *******/
  double run_time;
  double start_time = omp_get_wtime(); 
  
  int * global_frontier = malloc(sizeof(int) * nov);
  //for adequate vertices
  int * distances_global = malloc(sizeof(int) * nov);

  int * global_vertex_searched = malloc(sizeof(int) * nov);

  int i;
  for (i = 0; i < nov; ++i){
    global_frontier[i] = -1;
  }

  for (i = 0; i < nov; ++i){
    distances_global[i] = -1;
  }

  for (i = 0; i < nov; ++i){
    global_vertex_searched[i] = 0;
  }
  
    
  global_frontier[0] = source;
  printf("%d\n", source);
/* debug
  for (i = 0; i < nov; ++i){
    //printf("%d\n", row_ptr[i]);
    int row_d1 = row_ptr[i];
    int row_d2 = row_ptr[i+1];
    int j;
    for (j = row_d1; j < row_d2; ++j){
    //printf("%d\n", col_ind[j]);
    }
  }
*/
  //Id's start from 1
  distances_global[source] = 0;
  int global_queue_end = 1;
  int global_queue_start = 0;
  global_vertex_searched[source] = 1;
  
  int distance = 1;
  int num_threads;
  int ** frontier_arr = malloc(sizeof(int*) * OMP_NUM_THREADS);
  for (i = 0; i < OMP_NUM_THREADS; ++i){
      frontier_arr[i] = malloc(sizeof(int) * nov);
  }

  //preprocessing for maximum degree
  int j;
  int max_degree = 0;
  for (i = 0; i < nov; ++i){
    int d = row_ptr[i+1] - row_ptr[i];
    if (max_degree < d){
      max_degree = d;
    }
  }
  
    while(global_queue_start < global_queue_end){
    
    int th_num = global_queue_end - global_queue_start;
    if (th_num > OMP_NUM_THREADS)
      th_num = OMP_NUM_THREADS;
    #pragma omp parallel num_threads(th_num)
    {
        num_threads = omp_get_num_threads();
        int cur_thread = omp_get_thread_num();
        int size_of_f = global_queue_end - global_queue_start;
        int last_iter_end = size_of_f % num_threads;
        int num_of_v;
        int iter_num;
        if (last_iter_end != 0){
            num_of_v = size_of_f / num_threads + 1;
            iter_num = num_of_v;
            if (cur_thread == (num_threads-1))
                  iter_num = last_iter_end;
        }
        else{
            num_of_v = size_of_f / num_threads;
            iter_num = num_of_v;
        }
        int i;
        int iter_start = cur_thread * num_of_v + global_queue_start;
        int local_queue_start = 2;
        int local_queue_end = iter_num + 2;
        int size_of_frontier = max_degree * iter_num;
        if (size_of_frontier > nov){
            size_of_frontier = nov;
        }
        for (i = iter_start; i < iter_start + iter_num; ++i){
            frontier_arr[cur_thread][i-iter_start + local_queue_start] = global_frontier[i];
        }

        int * local_vertex_searched = malloc(sizeof(int) * nov);
        for (i = 0; i < nov; ++i){
            local_vertex_searched[i] = 0;
        }
        int local_queue_it; 
        int later_frontier_queue_start = iter_num;
        int later_frontier_queue_end = iter_num;
        for (local_queue_it = local_queue_start; local_queue_it < local_queue_end; ++local_queue_it){
            int cur_v = frontier_arr[cur_thread][local_queue_it];
            int neigh_f_mindelimit = row_ptr[cur_v];
            int neigh_f_maxdelimit = row_ptr[cur_v+1];
            int k;      
            for (k = neigh_f_mindelimit; k < neigh_f_maxdelimit; ++k){
                int vertex = col_ind[k];
                int v_s = local_vertex_searched[vertex];
                local_vertex_searched[vertex] = 1;
                //if clause or not?
                later_frontier_queue_end += 1 - v_s;
                frontier_arr[cur_thread][later_frontier_queue_end] = v_s * frontier_arr[cur_thread][later_frontier_queue_end] + vertex * (1 - v_s);
            }
        }
        frontier_arr[cur_thread][0] = later_frontier_queue_end;
        frontier_arr[cur_thread][1] = later_frontier_queue_start;
        free(local_vertex_searched);
      }
    #pragma omp barrier
    
    global_queue_start = global_queue_end;
    int k;
    for (k = 0; k < num_threads; ++k){
        int queue_end = frontier_arr[k][0];
        int queue_start = frontier_arr[k][1];
        for (i = queue_start; i <= queue_end; ++i){
            int vertex = frontier_arr[k][i];
            if (global_vertex_searched[vertex] == 0){
                global_frontier[global_queue_end] = vertex;
                global_queue_end++;
                global_vertex_searched[vertex] = 1;
                distances_global[vertex] = distance;
            }
        }
            
    }
    distance++;

  }

  free(global_frontier);
  free(global_vertex_searched);
  for (i = 0; i < OMP_NUM_THREADS; ++i){
    free(frontier_arr[i]);
  }
  free(frontier_arr);

  run_time = omp_get_wtime() - start_time;
  printf("threads and in %lf seconds\n", run_time);  
  

  //for(i = 0; i < global_queue_end; ++i){
  //  printf("%d, %d\n",i, global_frontier[i]);
  //}

  for (i = 0; i < nov; ++i){
    printf("%d ", distances_global[i]);
  }
  fflush(stdout);

  free(distances_global);
 
  
  free(row_ptr);
  free(col_ind);
 
  
   
  return 1;
}
