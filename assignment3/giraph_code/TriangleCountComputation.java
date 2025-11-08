package org.apache.giraph.examples.wiki;

import org.apache.giraph.graph.BasicComputation;
import org.apache.giraph.edge.Edge;
import org.apache.giraph.graph.Vertex;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.NullWritable;
import java.io.IOException;
import java.util.HashSet;
import java.util.Set;

/**
 * Triangle Counting using Node Iterator
 */
public class TriangleCountComputation extends BasicComputation<
    LongWritable, IntWritable, NullWritable, LongWritable> {

    @Override
    public void compute(
            Vertex<LongWritable, IntWritable, NullWritable> vertex,
            Iterable<LongWritable> messages) throws IOException {
        
        if (getSuperstep() == 0) {
            // Send neighbor list to all neighbors
            Set<Long> neighbors = new HashSet<>();
            for (Edge<LongWritable, NullWritable> edge : vertex.getEdges()) {
                neighbors.add(edge.getTargetVertexId().get());
            }
            
            // Send to all neighbors
            for (Long neighbor : neighbors) {
                sendMessage(new LongWritable(neighbor), 
                           new LongWritable(vertex.getId().get()));
            }
            vertex.setValue(new IntWritable(0));
            
        } else if (getSuperstep() == 1) {
            // Count triangles
            Set<Long> neighbors = new HashSet<>();
            for (Edge<LongWritable, NullWritable> edge : vertex.getEdges()) {
                neighbors.add(edge.getTargetVertexId().get());
            }
            
            int triangleCount = 0;
            for (LongWritable message : messages) {
                if (neighbors.contains(message.get())) {
                    triangleCount++;
                }
            }
            
            vertex.setValue(new IntWritable(triangleCount));
            vertex.voteToHalt();
        }
    }
}
