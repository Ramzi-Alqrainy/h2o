#GLM bench
import os, sys, time, csv, socket
sys.path.append('../py/')
sys.path.extend(['.','..'])
import h2o_cmd, h2o, h2o_hosts, h2o_browse as h2b, h2o_import as h2i, h2o_rf, h2o_jobs

csv_header = ('h2o_build','nMachines','nJVMs','Xmx/JVM','dataset','nTrainRows','nTestRows','nCols','trainParseWallTime','nfolds','glmBuildTime','testParseWallTime','scoreTime','AUC','AIC','error')

files      = {'Airlines'    : {'train': ('AirlinesTrain1x', 'AirlinesTrain10x'),          'test' : 'AirlinesTest'},
              'AllBedrooms' : {'train': ('AllBedroomsTrain1x', 'AllBedroomsTrain10x', 'AllBedroomsTrain100x'), 'test' : 'AllBedroomsTest'},
              'Airlines100'   : {'train': ('AirlinesTrain100x'), 'test' : 'AirlinesTest'},
             }
build = ""
debug = False
def doGLM(fs, folderPath, family, link, lambda_, alpha, nfolds, y, x, testFilehex, row):
    debug = False
    bench = "bench"
    if debug:
        print "DOING GLM DEBUG"
        bench = "bench/debug"
    date = '-'.join([str(z) for z in list(time.localtime())][0:3])
    for f in fs['train']:
        overallWallStart = time.time()
        pre              = ""
        if debug: pre    = "DEBUG"
        glmbenchcsv      = 'benchmarks/'+build+'/'+date+'/'+pre+'glmbench.csv'
        if not os.path.exists(glmbenchcsv):
            output = open(glmbenchcsv,'w')
            output.write(','.join(csv_header)+'\n')
        else:
            output = open(glmbenchcsv,'a')
        csvWrt = csv.DictWriter(output, fieldnames=csv_header, restval=None, 
                        dialect='excel', extrasaction='ignore',delimiter=',')
        try:
            java_heap_GB     = h2o.nodes[0].java_heap_GB
            importFolderPath = bench + "/" + folderPath
            if (f in ['AirlinesTrain1x','AllBedroomsTrain1x', 'AllBedroomsTrain10x', 'AllBedroomsTrain100x']): 
                csvPathname = importFolderPath + "/" + f + '.csv'
            else: 
                csvPathname = importFolderPath + "/" + f + "/*linked*"
            hex_key         = f + '.hex'
            hK              = folderPath + "Header.csv"    
            headerPathname  = importFolderPath + "/" + hK
            h2i.import_only(bucket='home-0xdiag-datasets', path=headerPathname)
            headerKey       = h2i.find_key(hK)
            trainParseWallStart = time.time()
            parseResult = h2i.import_parse(bucket           = 'home-0xdiag-datasets', 
                                           path             = csvPathname, 
                                           schema           = 'local', 
                                           hex_key          = hex_key,  
                                           header           = 1, 
                                           header_from_file = headerKey, 
                                           separator        = 44,
                                           timeoutSecs      = 7200,
                                           retryDelaySecs   = 5,
                                           pollTimeoutSecs  = 7200,
                                           doSummary        = False
                                          )

            parseWallTime  = time.time() - trainParseWallStart
            print "Parsing training file took ", parseWallTime ," seconds." 
            inspect_train  = h2o.nodes[0].inspect(parseResult['destination_key'], timeoutSecs=7200)
            inspect_test   = h2o.nodes[0].inspect(testFilehex, timeoutSecs=7200)

            nMachines      = 1 if len(h2o_hosts.hosts) is 0 else len(h2o_hosts.hosts)
            row.update( {'h2o_build'          : build,
                         'nMachines'          : nMachines,
                         'nJVMs'              : len(h2o.nodes),
                         'Xmx/JVM'            : java_heap_GB,
                         'dataset'            : f,
                         'nTrainRows'         : inspect_train['num_rows'],
                         'nTestRows'          : inspect_test['num_rows'],
                         'nCols'              : inspect_train['num_cols'],
                         'trainParseWallTime' : parseWallTime,
                         'nfolds'             : nfolds,
                        })

            params   =  {'y'                  : y,
                         'x'                  : x,
                         'family'             : family,
                         'link'               : link,
                         'lambda'             : lambda_,
                         'alpha'              : alpha,
                         'n_folds'            : nfolds,
                         'case_mode'          : "n/a",
                         'destination_key'    : "GLM("+f+")",
                         'expert_settings'    : 0,
                        }

            kwargs    = params.copy()
            glmStart  = time.time()
            glm       = h2o_cmd.runGLM(parseResult = parseResult, 
                                       timeoutSecs = 7200, 
                                       **kwargs)
            glmTime   = time.time() - glmStart
            row.update( {'glmBuildTime'       : glmTime,
                         #'AverageErrorOver10Folds'    : glm['GLMModel']['validations'][0]['err'],
                        })
            
            glmScoreStart = time.time()
            glmScore      = h2o_cmd.runGLMScore(key       = testFilehex,
                                                model_key = params['destination_key'])
            scoreTime     = time.time() - glmScoreStart
            if family == "binomial":
                row.update( {'scoreTime'          : scoreTime,
                             'AUC'                : glmScore['validation']['auc'],
                             'AIC'                : glmScore['validation']['aic'],
                             'error'              : glmScore['validation']['err'],
                            })
            else:
                row.update( {'scoreTime'          : scoreTime,
                             'AIC'                : glmScore['validation']['aic'],
                             'AUC'                : 'NA',
                             'error'              : glmScore['validation']['err'],
                            })
            csvWrt.writerow(row)
        finally:
            output.close()

if __name__ == '__main__':
    debug = sys.argv.pop(-1)
    build = sys.argv.pop(-1)
    h2o.parse_our_args()
    h2o_hosts.build_cloud_with_hosts(enable_benchmark_log=False)
    bench = "bench"
    if debug:
        bench = "bench/debug"
    airlinesTestParseStart      = time.time()
    hK                          =  "AirlinesHeader.csv"
    headerPathname              =  bench+"/Airlines" + "/" + hK
    h2i.import_only(bucket='home-0xdiag-datasets', path=headerPathname)
    headerKey                   = h2i.find_key(hK)
    testFile                    = h2i.import_parse(bucket='home-0xdiag-datasets', path=bench +'/Airlines/AirlinesTest.csv', schema='local', hex_key="atest.hex", header=1, header_from_file=headerKey, separator=44, doSummary=False,
                                  timeoutSecs=7200,retryDelaySecs=5, pollTimeoutSecs=7200)
    elapsedAirlinesTestParse    = time.time() - airlinesTestParseStart
    
    row = {'testParseWallTime' : elapsedAirlinesTestParse}
    x = "Year,Month,DayofMonth,DayofWeek,CRSDepTime,CRSArrTime,UniqueCarrier,CRSElapsedTime,Origin,Dest,Distance"
    doGLM(files['Airlines'], 'Airlines', 'binomial', 'logit', 1E-5, 0.5, 10, 'IsDepDelayed', x, testFile['destination_key'], row)

    allBedroomsTestParseStart   = time.time()
    x = 'areaname,state,metro,count1,count2,count3,count4,count5,count6,count7,count8,count9,count10,count11,count12,count13,count14,count15,count16,count17,count18,count19,count20,count21,count22,count23,count24,count25,count26,count27,count28,count29,count30,count31,count32,count33,count34,count35,count36,count37,count38,count39,count40,count41,count42,count43,count44,count45,count46,count47,count48,count49,count50,count51,count52,count53,count54,count55,count56,count57,count58,count59,count60,count61,count62,count63,count64,count65,count66,count67,count68,count69,count70,count71,count72,count73,count74,count75,count76,count77,count78,count79,count80,count81,count82,count83,count84,count85,count86,count87,count88,count89,count90,count91,count92,count93,count94,count95,count96,count97,count98,count99'
    hK                          =  "AllBedroomsHeader.csv"
    headerPathname              = bench+"/AllBedrooms" + "/" + hK
    h2i.import_only(bucket='home-0xdiag-datasets', path=headerPathname)
    headerKey                   = h2i.find_key(hK)

    testFile                    = h2i.import_parse(bucket='home-0xdiag-datasets', path=bench+'/AllBedrooms/AllBedroomsTest.csv', schema='local', hex_key="allBtest.hex", header=1, header_from_file=headerKey, separator=44, doSummary=False,
                                  timeoutSecs=7200,retryDelaySecs=5, pollTimeoutSecs=7200)

    elapsedAllBedroomsTestParse = time.time() - allBedroomsTestParseStart
    
    row = {'testParseWallTime' : elapsedAllBedroomsTestParse}
    doGLM(files['AllBedrooms'], 'AllBedrooms', 'gaussian', 'identity', 1E-4, 0.75, 10, 'medrent',x, testFile['destination_key'],row)
    ######################################Because Airline100x is risky, do it last
    bench = "bench"
    if debug:
        bench = "bench/debug"
    airlinesTestParseStart      = time.time()
    hK                          =  "AirlinesHeader.csv"
    headerPathname              =  bench+"/Airlines" + "/" + hK
    h2i.import_only(bucket='home-0xdiag-datasets', path=headerPathname)
    headerKey                   = h2i.find_key(hK)
    testFile                    = h2i.import_parse(bucket='home-0xdiag-datasets', path=bench +'/Airlines/AirlinesTest.csv', schema='local', hex_key="atest.hex", header=1, header_from_file=headerKey, separator=44, doSummary=False,
                                  timeoutSecs=7200,retryDelaySecs=5, pollTimeoutSecs=7200)
    elapsedAirlinesTestParse    = time.time() - airlinesTestParseStart
    
    row = {'testParseWallTime' : elapsedAirlinesTestParse}
    x = "Year,Month,DayofMonth,DayofWeek,CRSDepTime,CRSArrTime,UniqueCarrier,CRSElapsedTime,Origin,Dest,Distance"
    doGLM(files['Airlines100'], 'Airlines', 'binomial', 'logit', 1E-5, 0.5, 10, 'IsDepDelayed', x, testFile['destination_key'], row)

    
    h2o.tear_down_cloud()