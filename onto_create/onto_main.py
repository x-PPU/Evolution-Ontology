# This is a sample Python script.

# Press Umschalt+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import importTR as iTR
import importPLC as iPLC
import info_query as iQR


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    sc_number=["00","01","02","03","04","05","06","07","08","09","10","11","12","13","14"]
    folder_path ="./inputs/Sc"
    resource_path= "inputs/Model/paper-RDFmodelle2/"
    onto_filepath= "outputs/xPPU_onto.owl"
    onto_filename = "xPPU_onto.owl"
    iri = "http://example.org/onto-example.owl"

    print("================== generate ontology =====================")
    resource_data=iTR.readFile(iri, onto_filepath, folder_path,sc_number)
    iPLC.generateOnto(iri, onto_filepath,folder_path,sc_number)


    print("=============== running consistency checks ===============")
    iQR.query(onto_filepath,onto_filename,engine="owlready", showall=True)


    # model_graph = readRDF.load_Model(cad_path, simulation_path, componentlist_path,bpmn_path, plc_path, req_path,simReport_path,)
    # model_info= readRDF.read_data(model_graph)
    #
    # iri = "http://example.org/onto-example.owl"
    # metamodel_filepath = "inputs/Metamodel/Metamodel_MA.xmi"
    # onto_filepath = "./outputs/onto.owl"
    # onto_filename = "onto.owl"
    # taxonomy_file = "inputs/Taxonomy/Foerdermittel.csv"
    # # create_modelonto(iri, onto_file)
    #
    #
    # dic_data= im.readClass(metamodel_filepath)
    # print("===================== importing taxonomy =====================")
    # it.readTaxonomy(iri, onto_filepath, taxonomy_file)
    # print("====================== importing models ======================")
    # importModel.create_modelonto(iri, onto_filepath,model_info)
    # print("=============== running consistency checks ===============")
    # checkConsistency.check(onto_filepath,onto_filename,model_info, engine="owlready", showall=True)



