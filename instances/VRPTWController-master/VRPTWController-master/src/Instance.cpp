#include "Instance.h"

Instance::Instance(const char* instanciaPath) : dimension(0) {
    FILE* file = fopen(instanciaPath, "r");

    if(!file) {
        std::cout << "ERROR: Instance path wrong." << std::endl;
        exit(EXIT_FAILURE);
    }

    char name[64];
    char edgeWeightType[64];
    char aux[200];

    fscanf(file, "%s\n", name);
    this->name = std::string(name);
    fscanf(file, "%*[^\n]\n"); 
    fscanf(file, "%*[^\n]\n");
    fscanf(file, "%d %d\n", &this->maxVeh, &this->capacity);
    fscanf(file, "%*[^\n]\n"); 
    fscanf(file, "%*[^\n]\n");

    char* line = NULL;
    size_t len = 0;
    ssize_t read;

    while ((read = getline(&line, &len, file)) != -1) {
        int id, coordx, coordy, demand, ready_time, due_date, service_time;
        sscanf(line, "%d %d %d %d %d %d %d", &id, &coordx, &coordy, &demand, &ready_time, &due_date, &service_time);
        this->coordOrMatrix.push_back(std::vector< double >(3, 0));
        this->coordOrMatrix[id][0] = id; this->coordOrMatrix[id][1] = coordx; this->coordOrMatrix[id][2] = coordy; 
        this->demand.push_back(demand);
        this->l.push_back(ready_time);
        this->u.push_back(due_date);
        this->s.push_back(service_time);
        this->dimension += 1;
    }

    fclose(file);
}

double Instance::getEdgeWeight(int from, int to){
    return sqrt(pow((coordOrMatrix[from][1] - coordOrMatrix[to][1]), 2) + pow((coordOrMatrix[from][2] - coordOrMatrix[to][2]), 2));
}