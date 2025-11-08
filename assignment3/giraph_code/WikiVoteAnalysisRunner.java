package org.apache.giraph.examples.wiki;

import org.apache.giraph.conf.GiraphConfiguration;
import org.apache.giraph.job.GiraphJob;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

/**
 * Job runner for Wikipedia Vote Network analysis
 */
public class WikiVoteAnalysisRunner implements Tool {
    private Configuration conf;

    @Override
    public void setConf(Configuration conf) {
        this.conf = conf;
    }

    @Override
    public Configuration getConf() {
        return conf;
    }

    @Override
    public int run(String[] args) throws Exception {
        if (args.length != 3) {
            System.err.println("Usage: <algorithm> <input> <output>");
            System.err.println("Algorithms: wcc, triangle, pagerank");
            return -1;
        }

        String algorithm = args[0];
        String input = args[1];
        String output = args[2];

        GiraphConfiguration giraphConf = new GiraphConfiguration(getConf());
        
        // Set computation class based on algorithm
        switch(algorithm.toLowerCase()) {
            case "wcc":
                giraphConf.setComputationClass(WCCComputation.class);
                break;
            case "triangle":
                giraphConf.setComputationClass(TriangleCountComputation.class);
                break;
            case "pagerank":
                giraphConf.setComputationClass(PageRankComputation.class);
                break;
            default:
                System.err.println("Unknown algorithm: " + algorithm);
                return -1;
        }

        giraphConf.setVertexInputFormatClass(
            org.apache.giraph.io.formats.JsonLongDoubleFloatDoubleVertexInputFormat.class);
        giraphConf.setVertexOutputFormatClass(
            org.apache.giraph.io.formats.IdWithValueTextOutputFormat.class);

        GiraphJob job = new GiraphJob(giraphConf, "WikiVote-" + algorithm);
        FileOutputFormat.setOutputPath(job.getInternalJob(), new Path(output));
        giraphConf.set("mapreduce.input.fileinputformat.inputdir", input);

        return job.run(true) ? 0 : -1;
    }

    public static void main(String[] args) throws Exception {
        System.exit(ToolRunner.run(new WikiVoteAnalysisRunner(), args));
    }
}
