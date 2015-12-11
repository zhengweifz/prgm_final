library(shiny)
ur_data = read.csv("./allStatesMonthly.csv")
allYears = unique(ur_data$Date)
allYearsDate = as.Date(allYears)
allYearStr = unique(format(allYearsDate, "%Y"))
monthStr = c("01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12")
stateCodes = 1:50
names(stateCodes)= unique(ur_data$State)
shinyUI(pageWithSidebar(
  
  headerPanel("State Unemployment Rates"),
  
  sidebarPanel(
#     sliderInput("n", 
#                 "Years:", 
#                 value = 1,
#                 min = 1, 
#                 max = 477),
#     br(),
#   dateInput("urDate", "Month", value = '1976-01-01', min = "1976-01-01", max = "2015-09-01", format = "yyyy-mm-dd", startview = "month", weekstart = 0, language = "en", width = NULL),
    #br(),
    selectInput("urYr", "Year", allYearStr, selected = '1976', multiple = FALSE, selectize = TRUE, width = NULL, size = NULL),
    selectInput("urMonth", "Month", monthStr, selected = "01", multiple = FALSE, selectize = TRUE, width = NULL, size = NULL),
    HTML('<div id="centered" style="height:200px; width:10px;"></div>'),
    sliderInput("yrRange", "Unemployment Changes:",min = 1976, max = 2015, value = c(1976,2015), sep=""),
    HTML('<div id="centered" style="height:500px; width:10px;"></div>'),
    selectInput("stateIndex", "State", stateCodes, selected = "AL", multiple = FALSE, selectize = TRUE, width = NULL, size = NULL)
  ),
  
  mainPanel(
    plotOutput("urplot", height="400px"),
    h4("The worst 10 states in term of Unemployment changes"),
    br(),
    tableOutput("urRangeTable"),
    plotOutput("annualur", height="400px"),
    plotOutput("gdpur", height="400px"),
    plotOutput("gdpplot", height="400px"),
    plotOutput("urbytime", height="400px")
  )
))