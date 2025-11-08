package org.apache.giraph.examples.wiki;

import org.apache.giraph.graph.BasicComputation;
import org.apache.giraph.edge.Edge;
import org.apache.giraph.graph.Vertex;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.NullWritable;
import java.io.IOException;

/**
 * Weakly Connected Components - Label Propagation
 */
public class WCCComputation extends BasicComputation<
    LongWritable, LongWritable, NullWritable, LongWritable> {

    @Override
    public void compute(
            Vertex<LongWritable, LongWritable, NullWritable> vertex,
            Iterable<LongWritable> messages) throws IOException {
        
        long currentComponent = vertex.getValue().get();
        boolean changed = false;

        if (getSuperstep() == 0) {
            vertex.setValue(new LongWritable(vertex.getId().get()));
            currentComponent = vertex.getId().get();
            changed = true;
        } else {
            for (LongWritable message : messages) {
                long candidateComponent = message.get();
                if (candidateComponent < currentComponent) {
                    currentComponent = candidateComponent;
                    changed = true;
                }
            }
            
            if (changed) {
                vertex.setValue(new LongWritable(currentComponent));
            }
        }

        if (changed) {
            sendMessageToAllEdges(vertex, new LongWritable(currentComponent));
        } else {
            vertex.voteToHalt();
        }
    }
}
