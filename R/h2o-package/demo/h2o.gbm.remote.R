# This is a demo of H2O's GBM function
# It imports a data set, parses it, and prints a summary
# Then, it runs GBM on a subset of the dataset
library(h2o)
myIP = readline("Enter IP address of H2O server: ")
myPort = readline("Enter port number of H2O server: ")
remoteH2O = h2o.init(ip = myIP, port = as.numeric(myPort), startH2O = FALSE)

prostate.hex = h2o.uploadFile(remoteH2O, system.file("extdata", "prostate.csv", package="h2o"), "prostate.hex")
summary(prostate.hex)
prostate.gbm = h2o.gbm(x = setdiff(colnames(prostate.hex), "CAPSULE"), y = "CAPSULE", data = prostate.hex, n.trees = 10, interaction.depth = 5, shrinkage = 0.1)
print(prostate.gbm)
prostate.gbm2 = h2o.gbm(x = c("AGE", "RACE", "PSA", "VOL", "GLEASON"), y = "CAPSULE", data = prostate.hex, n.trees = 10, interaction.depth = 8, n.minobsinnode = 10, shrinkage = 0.2)
print(prostate.gbm2)

# This is a demo of H2O's GBM use of default parameters on iris dataset (three classes)
iris.hex = h2o.uploadFile(remoteH2O, system.file("extdata", "iris.csv", package="h2o"), "iris.hex")
summary(iris.hex)
iris.gbm = h2o.gbm(x = 1:4, y = 5, data = iris.hex)
print(iris.gbm)
