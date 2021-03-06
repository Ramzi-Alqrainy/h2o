##
##

setwd(normalizePath(dirname(R.utils::commandArgs(asValues=TRUE)$"f")))
source('../../findNSourceUtils.R')

test.columndereference <- function(conn) {
  Log.info('test column dereference')

  hdf <- h2o.uploadFile.FV(conn, locate('smalldata/jira/pub-180.csv'))
  otherhdf <- h2o.uploadFile.FV(conn, locate('smalldata/jira/v-11.csv'))

  column <- 'colgroup2'

  # get a single column out
  expect_that( dim(hdf[['colgroup2']]), equals(c(12,1)) )
  expect_that( dim(hdf[[column]]), equals(c(12,1)) )

  # NULL if column name doesn't exist
  expect_that( hdf[['col2group2']], equals(NULL))

  # we can overwrite a column
  hdf[['colgroup2']] <- hdf[['col2']]
  ldf <- as.data.frame( hdf[[ column ]] )[,1]
  expect_that(ldf, equals(c(2,4,6,11,3,4,6,11,2,4,6,11)) )

  # don't overwrite with the wrong number of rows
  expect_that( hdf[[column]] <- otherhdf[['ds1']], throws_error())
  expect_that( hdf[[column]] <- hdf[,2:3], throws_error() )

  testEnd()
}

doTest("test column dereference and assignment", test.columndereference)

