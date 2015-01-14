#!/usr/bin/python

# Load required modules
import sys, os, json, comet as C

def get_parser():
    # Parse arguments
    import argparse
    description = 'Runs CoMEt to find the optimal set M  '\
                  'of k genes for the weight function \Phi(M).'
    parser = argparse.ArgumentParser(description=description)

    # General parameters
    parser.add_argument('-o', '--output_prefix', required=True,
                        help='Output path prefix (TSV format).')
    parser.add_argument('-v', '--verbose', default=True, action="store_true",
                        help='Flag verbose output.')

    # Mutation data
    parser.add_argument('-m', '--mutation_matrix', required=True,
                        help='File name for mutation data.')
    parser.add_argument('-mf', '--min_freq', type=int, default=0, 
                        help='Minimum gene mutation frequency.')
    parser.add_argument('-pf', '--patient_file', default=None,
                        help='File of patients to be included.')
    parser.add_argument('-gf', '--gene_file', default=None,
                        help='File of genes to be included.')
    # Comet parameters
    parser.add_argument('-k', '--gene_set_size', type=int, required=True,
                        help='Gene set size.')
    parser.add_argument('-w', '--weight_func', default='exact',
                        help='Weight function to use.',
                        choices=C.weight_function_chars.keys())
    return parser


def run( args ):
    # Parse the arguments into shorter variable hadnles
    mutation_matrix = args.mutation_matrix
    gene_file = args.gene_file
    patient_file = args.patient_file
    min_freq = args.min_freq
    k = args.gene_set_size
    pvalthresh = 1.1
    wf = args.weight_func

    # Load the mutation data
    mutations = C.load_mutation_data(mutation_matrix, patient_file, gene_file, min_freq)
    m, n = mutations[0], mutations[1]
    if args.verbose:
        print '- Mutation data: %s genes x %s patients' % (m, n)

    # Set up the CoMEt run and then run exhaustively
    cMutations = C.convert_mutations_to_C_format(*mutations)
    iPatientToGenes, iGeneToCases, geneToNumCases, geneToIndex, indexToGene = cMutations
    genes = sorted(geneToIndex.keys(), key=lambda g: geneToIndex[g])

    C.precompute_factorials(max(m, n))
    C.set_weight(C.weight_function_chars[wf])
    results = C.exhaustive(k, m, n, iPatientToGenes, geneToNumCases, pvalthresh)
    C.free_factorials()

    # Parse the output
    solns, weights, tables, probs = results
    res = zip(solns, weights, tables, probs)
    res.sort(key=lambda arr: arr[1], reverse=True) # sort by weight decreasing
    solns   = [ sorted([genes[g] for g in geneset]) for geneset, w, t, p in res]
    weights = [ w for g, w, t, p in res]
    tables  = [ t for g, w, t, p in res]
    probs   = [ p for g, w, t, p in res]

    # Remove sets with a negative weight
    indices = [i for i in range(len(probs)) if probs[i] != -1]
    solns   = [solns[i] for i in indices]
    weights = [weights[i] for i in indices]
    tables  = [tables[i] for i in indices]
    probs   = [probs[i] for i in indices]
 
    # Output only sets, probs, and freqs as TSV
    with open("%s-k%s-%s-exhaustive.tsv" % (args.output_prefix, k, wf), "w") as outfile:
        output = [ "\t".join([ ", ".join(s), str(p), str(w)]) for s, p, w in zip(solns, probs, weights)]
        output.insert(0, "#Gene set\tP-value\tFreq\tWeight")
        outfile.write( "\n".join(output) )

if __name__ == "__main__": run( get_parser().parse_args(sys.argv[1:]) )    
