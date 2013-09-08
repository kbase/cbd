/*
Compression Based Distance (CBD) service

Compression-based distance (CBD) is a simple, rapid, and accurate method to
efficiently assess differences in microbiota samples.  CBD characterizes
the similarities between microbial communities via the amount of repetition
or overlap in order to determine microbial community distance.  CBD relies on
the fact that more repetitive data is the more it can be compressed.  By
combining 16S rRNA hypervariable tag data from different samples and assessing
the relative amounts of compression, there is a proxy for the similarities
between the communities.  The amount of compression is converted to a distance
with a minimum of 0 and a maximum of 1 by taking compression gained by combining
the datasets over the total compressed size of the individual datasets.

*/

module CompressionBasedDistance
{

	/* ************************************************************************************* */
	/* CBD FUNCTIONS */
	/* ************************************************************************************* */
	
	/* Input parameters for build_matrix function
	
		list<string> node_ids - List of Shock node ids for sequence files
		string format - Format of input sequence files ('fasta', 'fastq', etc.)
		string scale - Scale for distance matrix values ('std' or 'inf')
			
	*/
	typedef structure {
		list<string> node_ids;
		string format;
		string scale;
	} BuildMatrixParams;
	
	/*
      Build a distance matrix from a set of sequence files for microbiota
      comparisons.  Compression based distance uses the relative compression
      of combined and individual datasets to quantify overlaps between
      microbial communities.  Returns an array of lines where each line is a
      line in the distance matrix in csv format.
	*/
	funcdef build_matrix(BuildMatrixParams input)
		returns(list<string> output) authentication required;
	
};