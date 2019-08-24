#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "common.h"
#include <omp.h>


#define TRAIN_NUM 19000
#define TEST_NUM 1000
#define DIMENSIONS 16

#define THREADS_PER_BLOCK 256
#define N TRAIN_NUM + THREADS_PER_BLOCK - 1

__global__ void vector_distance(int *a, int *b, int *c) {
  int index = (THREADS_PER_BLOCK * blockIdx.x) + threadIdx.x;
  if (index < TRAIN_NUM){
	  int dim;
	  int distance = 0;
	  int one_dim_dif;
	  for (dim = 0; dim < 16; ++dim){
		 one_dim_dif = a[index * DIMENSIONS + dim] - b[dim];
		 distance += one_dim_dif * one_dim_dif;
	  }
	  //stores index as the point in train
	  c[index] = distance;
  }
}

int main(){
	
	FILE * train_file;
	FILE * test_file;
	FILE * output_file;
	train_file = fopen("train.txt", "r");
	test_file = fopen("test.txt", "r");
	
	int train_data[TRAIN_NUM * DIMENSIONS];
	int test_data[TEST_NUM][DIMENSIONS];
	int output[TEST_NUM];
	
	int i,j;
	
	char singleLine[150];
	char * cdim;
	char * str;
	int dim;
	int line = 0;
	
	while (!feof(train_file)){
		dim = 0;
		fgets(singleLine, 150, train_file);
		str = strdup(singleLine);
		while (cdim = strsep(&str, ",")){
			train_data[line * DIMENSIONS + dim++] = atoi(cdim);
		}
		++line;
	}
	
	fclose(train_file);
	
	line = 0;
	while (!feof(test_file)){
		dim = 0;
		fgets(singleLine, 150, test_file);
		str = strdup(singleLine);
		while (cdim = strsep(&str, ",")){
			test_data[line][dim++] = atoi(cdim);
		}
		++line;
	}
	
	fclose(test_file);
	
	size_t size_train = TRAIN_NUM * DIMENSIONS * sizeof(int);
	size_t size_dist  = TRAIN_NUM * sizeof(int);
	size_t size_testpoint  = DIMENSIONS * sizeof(int);
	
	int * dist;
	cudaMallocHost( (void**) &dist, size_dist);

	int * d_train, * d_dist, * d_testpoint;
	
	double run_time;
	double start_time = omp_get_wtime();
	
	cudaCheck(cudaMalloc( (void **) &d_train, size_train));
	cudaCheck(cudaMalloc( (void **) &d_dist, size_dist));
	cudaCheck(cudaMalloc( (void **) &d_testpoint, size_testpoint));
	
	cudaCheck(cudaPeekAtLastError());
	
	int min, point_min;
	cudaCheck(cudaMemcpy(d_train, train_data, size_train, cudaMemcpyHostToDevice));
	for (i = 0; i < TEST_NUM; ++i){
		point_min = -1;
		min = 999999;
		cudaCheck(cudaMemcpy(d_testpoint, test_data[i], size_testpoint, cudaMemcpyHostToDevice));
		vector_distance<<<N/THREADS_PER_BLOCK, THREADS_PER_BLOCK>>>
			(d_train, d_testpoint, d_dist);
		cudaCheck(cudaMemcpy(dist, d_dist, size_dist, cudaMemcpyDeviceToHost));
		for (j = 0; j < TRAIN_NUM; ++j){
			if (dist[j] < min){
				min = dist[j];
				point_min = j;
			}
		}
		output[i] = point_min;
	}
	
	run_time = omp_get_wtime() - start_time;
	printf("Total time: %6.3f\n", run_time);
	
	output_file = fopen("output.txt", "w");
	
	for (i = 0; i < TRAIN_NUM; ++i)
		fprintf(output_file, "%d\n", output[i]);

	
	fclose(output_file);
	
	cudaFreeHost(dist);
	
	cudaFree(d_train);
	cudaFree(d_testpoint);
	cudaFree(d_dist);
}
