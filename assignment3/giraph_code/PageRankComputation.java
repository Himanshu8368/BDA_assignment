package org.apache.giraph.examples.wiki;

import org.apache.giraph.graph.BasicComputation;
import org.apache.giraph.edge.Edge;
import org.apache.giraph.graph.Vertex;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.NullWritable;
import java.io.IOException;

/**
 * PageRank Implementation
 */
public class PageRankComputation extends BasicComputation<
    LongWritable, DoubleWritable, NullWritable, DoubleWritable> {

    private static final int MAX_SUPERSTEPS = 30;
    private static final double DAMPING_FACTOR = 0.85;

    @Override
    public void compute(
            Vertex<LongWritable, DoubleWritable, NullWritable> vertex,
            Iterable<DoubleWritable> messages) throws IOException {
        
        if (getSuperstep() == 0) {
            vertex.setValue(new DoubleWritable(1.0));
        } else {
            double sum = 0;
            for (DoubleWritable message : messages) {
                sum += message.get();
            }
            
            double newValue = (1 - DAMPING_FACTOR) + DAMPING_FACTOR * sum;
            vertex.setValue(new DoubleWritable(newValue));
        }

        if (getSuperstep() < MAX_SUPERSTEPS) {
            long edges = vertex.getNumEdges();
            if (edges > 0) {
                double msgValue = vertex.getValue().get() / edges;
                sendMessageToAllEdges(vertex, new DoubleWritable(msgValue));
            }
        } else {
            vertex.voteToHalt();
        }
    }
}
