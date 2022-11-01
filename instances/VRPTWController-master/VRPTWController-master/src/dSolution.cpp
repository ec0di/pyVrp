#include "dSolution.h"
#define EPS 1e-6

bool dSolution::checkSolution() {
    double solCost          = 0;
    vector< bool > isNodeIn = vector< bool >(instance->dimension, false);
    isNodeIn[0]             = true;

    if(routes.size() > instance->maxVeh) {
        std::cout << "Max nb. of vehicles was violated: " << routes.size() << " > V=" << instance->maxVeh << std::endl;
        return false;
    }

    for(vector< int > route : routes) {
        if(route[route.size() - 1] == 0)
            route.pop_back();

        double travelTime = 0.0;
        double edgeCost = round(instance->getEdgeWeight(0, route.at(0)));
        solCost += edgeCost;
        
        travelTime = max(travelTime + edgeCost, (double) instance->l[route.at(0)]);
        // std::cout << "(0," << route.at(0) << ") c" << edgeCost << " t" << travelTime << std::endl;
        if(travelTime > instance->u[route.at(0)] + EPS) { // checks TW violation
            std::cout << "TW of " << route.at(0) << " ([" << instance->l[route.at(0)]
                << "," << instance->u[route.at(0)] << "]) was violated (arrival time = " << travelTime << ")" << std::endl;
            return false;
        }

        int demanda = instance->demand[route.at(0)];
        if(demanda > instance->capacity)
            return false;

        isNodeIn[route.at(0)] = !(isNodeIn[route.at(0)] && true);

        for(int i = 1; i < route.size(); i++) {

            edgeCost = round(instance->getEdgeWeight(route.at(i - 1), route.at(i)));
            solCost += edgeCost;

            travelTime = max(travelTime + edgeCost + (double) instance->s[route.at(i - 1)], (double) instance->l[route.at(i)]);
            // std::cout << "("<< route.at(i - 1) << "," << route.at(i) << ") c" << edgeCost << " t" << travelTime << std::endl;

            if(travelTime > instance->u[route.at(i)] + EPS) { // checks TW violation
                std::cout << "TW of " << route.at(i) << " ([" << instance->l[route.at(i)] 
                    << "," << instance->u[route.at(i)] << "]) was violated (arrival time = " << travelTime << ")" << std::endl;
                return false;
            }

            demanda += instance->demand[route.at(i)];
            if(demanda > instance->capacity)
                return false;

            isNodeIn[route.at(i)] = !(isNodeIn[route.at(i)] && true);
        }
        edgeCost = round(instance->getEdgeWeight(route.at(route.size() - 1), 0));
        solCost += edgeCost;
        travelTime = max(travelTime + edgeCost + (double) instance->s[route.at(route.size() - 1)], (double) instance->l[0]);
        // std::cout << "("<< route.at(route.size() - 1) << "," << 0 << ") c" << edgeCost << " t" << travelTime << std::endl;
        if(travelTime > instance->u[0] + EPS) { // checks TW violation
            std::cout << "TW of " << 0 << " ([" << instance->l[0] 
                << "," << instance->u[0] << "]) was violated (arrival time = " << travelTime << ")" << std::endl;
            return false;
        }
    }
    
    for(int i=0; i < instance->dimension; i++) {
        if(!isNodeIn[i])
            std::cout << "Customer " << i << " was not visited or was visited more than once!" << std::endl;
    }
    for(bool i : isNodeIn)
        if(!i) 
            return false;
    this->cost = solCost;
    return true;
}

bool dSolution::parseLine(char* line) {
    bool flag   = false;
    char* token = strtok(line, " ");

    if(strstr(token, "Route") != NULL) {
        vector< int > route;
        token = strtok(NULL, " ");
        token = strtok(NULL, " ");

        while(token != NULL) {
            route.push_back(atoi(token));
            token = strtok(NULL, " ");
        }

        routes.push_back(route);
    } else if(strstr(token, "Cost") != NULL) {
        token = strtok(NULL, " ");
        cost  = atof(token);
        flag  = true;
    }

    return flag;
}

string dSolution::getStats(std::chrono::high_resolution_clock::time_point beginTime, std::chrono::high_resolution_clock::time_point endTime, int passMark) {
    // std::chrono::high_resolution_clock::time_point t1 = std::chrono::high_resolution_clock::now();
    std::chrono::milliseconds ms = std::chrono::duration_cast< std::chrono::milliseconds >(endTime - beginTime);

    char stats[256];
    sprintf(stats, "%.1lf %.3lf %.3lf\n", cost, ms.count() / 1000.0, (ms.count() / 1000.0) * ((double)passMark / CPU_BASE_REF));
    return string(stats);
}
