// ============================================
// NEO4J CYPHER QUERIES - Wikipedia Vote Network
// Complete Implementation
// ============================================

// STEP 1: CREATE CONSTRAINTS
// ============================================
CREATE CONSTRAINT unique_user_id IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

// STEP 2: LOAD DATA
// ============================================

// Load nodes
LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
CREATE (:User {id: toInteger(row.id)});

// Verify nodes loaded
MATCH (n:User) RETURN count(n) AS totalNodes;

// Load edges
LOAD CSV WITH HEADERS FROM 'file:///edges.csv' AS row
MATCH (u1:User {id: toInteger(row.src)}), (u2:User {id: toInteger(row.dst)})
CREATE (u1)-[:VOTED_FOR]->(u2);

// Verify edges loaded
MATCH ()-[r:VOTED_FOR]->() RETURN count(r) AS totalEdges;

// STEP 3: CREATE GRAPH PROJECTION
// ============================================

// Drop existing projection if exists
CALL gds.graph.drop('wikiVoteGraph', false);

// Create new projection
CALL gds.graph.project(
  'wikiVoteGraph',
  'User',
  {
    VOTED_FOR: {
      orientation: 'NATURAL'
    }
  }
) YIELD graphName, nodeCount, relationshipCount;

// STEP 4: BASIC STATISTICS
// ============================================

MATCH (n:User) 
WITH count(n) AS nodes
MATCH ()-[r:VOTED_FOR]->()
RETURN nodes, count(r) AS edges;

// STEP 5: WEAKLY CONNECTED COMPONENTS (WCC)
// ============================================

// Get WCC statistics
CALL gds.wcc.stats('wikiVoteGraph')
YIELD componentCount, componentDistribution
RETURN componentCount, 
       componentDistribution.max AS largestWCCSize,
       componentDistribution.min AS smallestWCCSize;

// Write WCC to nodes
CALL gds.wcc.write('wikiVoteGraph', {writeProperty: 'wcc'})
YIELD nodePropertiesWritten, componentCount;

// Count edges in largest WCC
MATCH (n:User)-[r:VOTED_FOR]->(m:User)
WHERE n.wcc = m.wcc
WITH n.wcc AS component, count(r) AS edges
ORDER BY edges DESC
LIMIT 1
RETURN component, edges AS edgesInLargestWCC;

// Get WCC distribution
MATCH (n:User)
WITH n.wcc AS component, count(*) AS size
RETURN size, count(*) AS numComponents
ORDER BY size DESC;

// STEP 6: STRONGLY CONNECTED COMPONENTS (SCC)
// ============================================

// Note: SCC requires directed graph analysis
// This is an approximation using available algorithms

// Using WCC as proxy (for undirected connectivity)
CALL gds.wcc.stream('wikiVoteGraph')
YIELD nodeId, componentId
WITH componentId, count(*) AS size
ORDER BY size DESC
LIMIT 10
RETURN componentId, size;

// STEP 7: TRIANGLE COUNTING
// ============================================

// Count total triangles
CALL gds.triangleCount.stats('wikiVoteGraph')
YIELD globalTriangleCount
RETURN globalTriangleCount AS totalTriangles;

// Write triangle counts to nodes
CALL gds.triangleCount.write('wikiVoteGraph', {
  writeProperty: 'triangles'
})
YIELD globalTriangleCount, nodeCount;

// Top nodes by triangle participation
CALL gds.triangleCount.stream('wikiVoteGraph')
YIELD nodeId, triangleCount
RETURN gds.util.asNode(nodeId).id AS userId, triangleCount
ORDER BY triangleCount DESC
LIMIT 10;

// STEP 8: CLUSTERING COEFFICIENT
// ============================================

// Average clustering coefficient
CALL gds.localClusteringCoefficient.stats('wikiVoteGraph')
YIELD averageClusteringCoefficient
RETURN averageClusteringCoefficient;

// Write clustering coefficient
CALL gds.localClusteringCoefficient.write('wikiVoteGraph', {
  writeProperty: 'clusteringCoef'
})
YIELD averageClusteringCoefficient, nodeCount;

// Top nodes by clustering coefficient
CALL gds.localClusteringCoefficient.stream('wikiVoteGraph')
YIELD nodeId, localClusteringCoefficient
WHERE localClusteringCoefficient > 0
RETURN gds.util.asNode(nodeId).id AS userId, 
       localClusteringCoefficient
ORDER BY localClusteringCoefficient DESC
LIMIT 10;

// Fraction of closed triangles
MATCH (n:User)
WITH sum(n.triangles) AS totalTriangleParticipations
MATCH ()-[r:VOTED_FOR]->()
WITH totalTriangleParticipations, count(r) AS edges
RETURN totalTriangleParticipations / 3.0 AS triangles,
       (totalTriangleParticipations / 3.0) * 3.0 / (edges * (edges - 1.0) / 2.0) 
       AS fractionClosedTriangles;

// STEP 9: DEGREE CENTRALITY
// ============================================

// In-degree and out-degree distribution
CALL gds.degree.stream('wikiVoteGraph', {orientation: 'NATURAL'})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).id AS userId, score AS degree
ORDER BY score DESC
LIMIT 10;

// STEP 10: PAGERANK
// ============================================

// Calculate PageRank
CALL gds.pageRank.stream('wikiVoteGraph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).id AS userId, score
ORDER BY score DESC
LIMIT 10;

// Write PageRank
CALL gds.pageRank.write('wikiVoteGraph', {
  writeProperty: 'pagerank',
  maxIterations: 20,
  dampingFactor: 0.85
})
YIELD nodePropertiesWritten, ranIterations;

// STEP 11: BETWEENNESS CENTRALITY
// ============================================

// Sample-based betweenness (full computation is expensive)
CALL gds.betweenness.stream('wikiVoteGraph', {
  samplingSize: 1000,
  samplingSeed: 42
})
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).id AS userId, score
ORDER BY score DESC
LIMIT 10;

// STEP 12: DIAMETER ESTIMATION
// ============================================

// All shortest paths (WARNING: Very expensive on full graph!)
// Use only on largest SCC or sample

// Sample-based diameter estimation
MATCH (start:User)
WITH start
ORDER BY rand()
LIMIT 100
CALL {
  WITH start
  MATCH path = (start)-[:VOTED_FOR*]->(end:User)
  RETURN length(path) AS pathLength
  ORDER BY pathLength DESC
  LIMIT 1
}
RETURN max(pathLength) AS estimatedDiameter,
       percentileCont(pathLength, 0.9) AS effective90Diameter;

// STEP 13: COMMUNITY DETECTION (Louvain)
// ============================================

// Detect communities
CALL gds.louvain.stream('wikiVoteGraph')
YIELD nodeId, communityId
WITH communityId, count(*) AS size
RETURN communityId, size
ORDER BY size DESC
LIMIT 20;

// Write communities
CALL gds.louvain.write('wikiVoteGraph', {
  writeProperty: 'community'
})
YIELD communityCount, modularity;

// STEP 14: COMPREHENSIVE SUMMARY QUERY
// ============================================

MATCH (n:User) 
WITH count(n) AS totalNodes
MATCH ()-[r:VOTED_FOR]->()
WITH totalNodes, count(r) AS totalEdges
MATCH (n:User)
WITH totalNodes, totalEdges, 
     sum(n.triangles)/3.0 AS triangles,
     avg(n.clusteringCoef) AS avgClustering,
     max(n.pagerank) AS maxPageRank
RETURN 
  totalNodes AS nodes,
  totalEdges AS edges,
  triangles,
  avgClustering AS averageClusteringCoefficient,
  maxPageRank,
  totalEdges * 1.0 / totalNodes AS avgDegree;

// STEP 15: EXPORT RESULTS
// ============================================

// Export node metrics to CSV
CALL apoc.export.csv.query(
  "MATCH (n:User) 
   RETURN n.id AS userId, 
          n.triangles AS triangles,
          n.clusteringCoef AS clusteringCoef,
          n.pagerank AS pagerank,
          n.community AS community
   ORDER BY n.pagerank DESC",
  "node_metrics.csv",
  {}
);

// STEP 16: PERFORMANCE TIMING QUERIES
// ============================================

// Time WCC computation
CALL gds.wcc.stream('wikiVoteGraph')
YIELD nodeId, componentId
RETURN count(*) AS nodesProcessed;
// Note: Check execution time in Neo4j Browser profile

// Time Triangle Count
CALL gds.triangleCount.stream('wikiVoteGraph')
YIELD nodeId, triangleCount
RETURN sum(triangleCount)/3 AS totalTriangles;

// Time PageRank
CALL gds.pageRank.stream('wikiVoteGraph', {maxIterations: 20})
YIELD nodeId, score
RETURN count(*) AS nodesRanked;

// STEP 17: CLEANUP
// ============================================

// Remove computed properties (optional)
MATCH (n:User)
REMOVE n.wcc, n.triangles, n.clusteringCoef, n.pagerank, n.community;

// Drop graph projection
CALL gds.graph.drop('wikiVoteGraph');

// Delete all data (if needed)
MATCH (n:User)
DETACH DELETE n;

// ============================================
// GROUND TRUTH VERIFICATION QUERIES
// ============================================

// Compare with ground truth
// Expected: 7,115 nodes, 103,689 edges

MATCH (n:User) 
WITH count(n) AS actualNodes
MATCH ()-[r:VOTED_FOR]->()
WITH actualNodes, count(r) AS actualEdges
RETURN 
  actualNodes,
  7115 AS expectedNodes,
  actualNodes = 7115 AS nodesMatch,
  actualEdges,
  103689 AS expectedEdges,
  actualEdges = 103689 AS edgesMatch;

// ============================================
// PERFORMANCE OPTIMIZATION TIPS
// ============================================

// 1. Create indexes for faster lookups
CREATE INDEX user_id_index IF NOT EXISTS FOR (u:User) ON (u.id);

// 2. Use PROFILE to analyze query performance
PROFILE MATCH (n:User)-[:VOTED_FOR]->(m:User)
RETURN count(*);

// 3. Use EXPLAIN to see query plan
EXPLAIN MATCH (n:User)-[:VOTED_FOR*2]->(m:User)
RETURN count(*);

// 4. For large operations, increase memory
// Add to neo4j.conf:
// dbms.memory.heap.initial_size=2g
// dbms.memory.heap.max_size=4g

// ============================================
// END OF QUERIES
// ============================================
