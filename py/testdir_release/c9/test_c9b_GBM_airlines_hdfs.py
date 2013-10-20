import unittest
import random, sys, time, re
sys.path.extend(['.','..','py'])

import h2o, h2o_cmd, h2o_hosts, h2o_browse as h2b, h2o_import as h2i, h2o_glm, h2o_util, h2o_rf, h2o_jobs as h2j
import h2o_common

class releaseTest(h2o_common.ReleaseCommon, unittest.TestCase):

    def test_GBM_ec2_airlines(self):

        h2o.beta_features = False

        files = [
                 ('datasets', 'airlines_all.csv', 'airlines_all.hex', 1800, 'IsDepDelayed')
                ]

        for importFolderPath, csvFilename, trainKey, timeoutSecs, response in files:
            h2o.beta_features = False #turn off beta_features
            # PARSE train****************************************
            csvPathname = importFolderPath + "/" + csvFilename
            
            start = time.time()
            parseResult = h2i.import_parse(path=csvPathname, schema='hdfs', hex_key=trainKey, 
                timeoutSecs=timeoutSecs)
            elapsed = time.time() - start
            print "parse end on ", csvFilename, 'took', elapsed, 'seconds',\
                "%d pct. of timeout" % ((elapsed*100)/timeoutSecs)
            print "parse result:", parseResult['destination_key']

            # GBM (train)****************************************
            for depth in [5,15,25,40]:
                params = {
                    'destination_key': "GBMKEY",
                    'learn_rate': .2,
                    'nbins': 1024,
                    'ntrees': 10,
                    'max_depth': depth,
                    'min_rows': 10,
                    'response': response,
                    'ignored_cols_by_name': 'CRSDepTime,CRSArrTime,ActualElapsedTime,CRSElapsedTime,AirTime,ArrDelay,DepDelay,TaxiIn,TaxiOut,Cancelled,CancellationCode,Diverted,CarrierDelay,WeatherDelay,NASDelay,SecurityDelay,LateAircraftDelay,IsArrDelayed'
                }
                print "Using these parameters for GBM: ", params
                kwargs = params.copy()
                h2o.beta_features = True
                start = time.time()
                print "Start time is: ", time.time()
                #noPoll -> False when GBM finished
                GBMResult = h2o_cmd.runGBM(parseResult=parseResult, noPoll=True,timeoutSecs=timeoutSecs,**kwargs)
                h2j.pollWaitJobs(pattern="GBMKEY",timeoutSecs=1800,pollTimeoutSecs=1800)
                print "Finished time is: ", time.time()
                elapsed = time.time() - start
                print "GBM training completed in", elapsed, "seconds. On dataset: ", csvFilename
                #GBMView = h2o_cmd.runGBMView(model_key='GBMKEY')
                #print GBMView['gbm_model']['errs']

if __name__ == '__main__':
    h2o.unit_main()
