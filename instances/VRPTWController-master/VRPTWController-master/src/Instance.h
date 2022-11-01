#ifndef INSTANCE_H
#define INSTANCE_H

#include <iostream>
#include <math.h>
#include <string.h>
#include <string>
#include <vector>

class Instance {
  public:
    int dimension;
    int capacity;
    int maxVeh;
    std::string name;
    std::vector< int > demand;
    std::vector< int > s; // service time
    std::vector< int > l; // TW's lower bound 
    std::vector< int > u; // TW's upper bound
    std::vector< std::vector< double > > coordOrMatrix;

    Instance() {}
    Instance(const char* instanciaPath);
    // Get edge weight between two vertices "from" and "to"
    double getEdgeWeight(int from, int to);
};

#endif