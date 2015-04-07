Compression-Based Distance
==========================

Compression-based distance (CBD) is a simple, rapid, and accurate method to
efficiently assess differences in microbiota samples.  CBD characterizes
the similarities between microbial communities via the amount of repetition
or overlap in order to determine microbial community distance.  CBD relies on
the fact that more repetitive data is the more it can be compressed.  By
combining 16S rRNA hypervariable tag data from different samples and assessing
the relative amounts of compression, there is a proxy for the similarities
between the communities.  The amount of compression is converted to a distance
by taking compression gained by combining the datasets over the total
compressed size of the individual datasets.  The distance has a value with a
minimum of 0 meaning the communities are the same and a maximum of 1 meaning
the communities are completely different.

Configuration Variables
-----------------------

The Compression-Based Distance server supports the following configuration variables:

* **default_url**: The default URL for this server's service endpoint.
* **shock_url**: URL for the Shock service endpoint. The Shock service is used to
  transfer input sequence files to the server and return the computed distance matrix
  file to the client.
* **userandjobstate_url**: URL of the User and Job State service endpoint.  The UJS
  service is used to manage the jobs that build a distance matrix.
* **work_folder_path**: Path to work folder containing a sub-folders for each running
  job.  The intermediate files created by the build_matrix() method are stored in
  this location.
* **num_pool_processes**: Number of processes in multiprocess pool.  A larger value
  increases the number of tasks running in parallel when building a distance matrix.
  Default value is 5.

