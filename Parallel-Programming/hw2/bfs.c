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
    #define OMP_NUM_THREADS 16
#endif

#define bool int
#define true 1
#define false 0

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
  
  //for adequate vertices
  int * colors_global = malloc(sizeof(int) * nov);
  int i;

  for (i = 0; i < nov; ++i){
    colors_global[i] = 0;
  }

  
    
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
  
  //preprocessing for maximum degree
  int j;
  int max_degree = 0;
  for (i = 0; i < nov; ++i){
    int d = row_ptr[i+1] - row_ptr[i];
    if (max_degree < d){
      max_degree = d;
    }
  }
  
  bool * changedArr = malloc(sizeof(bool) * OMP_NUM_THREADS);
  bool isChanged = true;

    #pragma omp parallel 
    {
        int num_threads = omp_get_num_threads();
        int cur_thread = omp_get_thread_num();
        int i;
        
        
       // int * vertex_color_set = malloc(sizeof(int) * iter_num);
       // for (i = 0; i < iter_num; ++i){
       //     vertex_color_set[i] = 0;
       // }


        int * forbidden_colors = malloc(sizeof(int) * (10000));
        for (i = 0; i < 10000; ++i){
            forbidden_colors[i] = -1;
        }
        //coloring
        //int * local_row_ptr = malloc(sizeof(int) * iter_num);
        //local_row_ptr[0] = 0;

        //int * local_col_ind = malloc(sizeof(int) * iter_num * max_degree);
        //for (i = 1; i < iter_num+1; ++i){
        //    int v = vertex_set[i-1];
        //    int low_d = row_ptr[v];
        //    int high_d = row_ptr[v+1];
        //    int dif = high_d - low_d;
        //    local_row_ptr[i] = local_row_ptr[i-1] + dif;
        //    for (j = 0; j < dif; ++j){
        //        local_col_ind[local_row_ptr[i-1] + j] = col_ind[low_d+j];
        //    }
        //    //get all of vertex,row as such or?
        //}
        
        #pragma omp for schedule(guided)
        for (i = 0; i < nov; ++i){
            int low_d = row_ptr[i];
            int high_d = row_ptr[i+1];
            int j;
            for (j = low_d; j < high_d; ++j){
                int neigh = col_ind[j];
                int neigh_color = colors_global[neigh];
                forbidden_colors[neigh_color] = i;
            }
            j = 1;
            while(forbidden_colors[j] == i){
                ++j;
            }
            colors_global[i] = j;
        }

        changedArr[cur_thread] = true;
        bool changed;
        while (isChanged){
            changed = false;
            #pragma omp for schedule(guided)
            for (i = 0; i < nov; ++i){
                int low_d = row_ptr[i];
                int high_d = row_ptr[i+1];
                int j;
                for (j = low_d; j < high_d; ++j){
                    int neigh = col_ind[j];
                    if (neigh > i)
                        continue;
                    else{
                        int neigh_color = colors_global[neigh];
                        forbidden_colors[neigh_color] = i;
                    }
                }
                if (forbidden_colors[colors_global[i]] == i){
                    changed = true;
                    j = 1;
                    while(forbidden_colors[j] == i){
                        ++j;
                    }
                colors_global[i] = j;
                }
            }
            changedArr[cur_thread] = changed;
            #pragma omp barrier
            #pragma omp single
            {
                isChanged = false;
                for(i = 0; i < num_threads; ++i){
                    if(changedArr[i]){
                        isChanged = true;
                        break;
                    }       
                }
            }
        }

      
      free(forbidden_colors);
      }
    #pragma omp barrier
    


    //add while loop: first isConflict, set it to False, if any set to True
/*
    for (i = 0; i < nov; ++i){
        int low_d = row_ptr[i];
        int high_d = row_ptr[i+1];
        int j;
        for (j = low_d; j < high_d; ++j){
            int neigh = col_ind[j];
            g_forbidden_colors[colors_global[neigh]] = i; 
        }
        j = 1;
        while(g_forbidden_colors[j] == i){
            ++j;
        }
        colors_global[i] = j;
    }
            
*/


  run_time = omp_get_wtime() - start_time;
  printf("threads and in %lf seconds\n", run_time);  
  


  //for (i = 0; i < nov; ++i){
  //  printf("%d ", colors_global[i]);
  //}
  //fflush(stdout);
    int color_max = 0;
    for (i = 0; i < nov; ++i){
        if(color_max < colors_global[i])
            color_max = colors_global[i];
    }
    printf("%d\n", color_max);

  free(colors_global);
  free(changedArr);
  
  free(row_ptr);
  free(col_ind);
 
  
   
  return 1;
}
