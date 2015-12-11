library(shiny)
shinyapps::showLogs() 
if (!require("ggplot2")) {
  install.packages("ggplot2", dependencies = TRUE)
  library(ggplot2)
}
if (!require("maptools")) {
  install.packages("maptools", dependencies = TRUE)
  library(maptools)
}
if (!require("mapproj")) {
  install.packages("mapproj", dependencies = TRUE)
  library(mapproj)
}
# before you run our codes, please download map data files from
#https://www.arcgis.com/home/item.html?id=f7f805eb65eb4ab787a0a3e1116ca7e5
#unzip the files, which contains states.shp into the server.R folder
gpclibPermit()
us50_shp <- readShapePoly("./states.shp")
us50_df <- as.data.frame(us50_shp)
us50_points <- sp2tmap(us50_shp)
names(us50_points) <- c("id", "x", "y")
us50 <- merge(x = us50_df, y = us50_points, by.x = "DRAWSEQ", by.y = "id")
cont_us <- us50[us50$STATE_ABBR != "HI" & us50$STATE_ABBR != "AK", ]
ak <- us50[us50$STATE_ABBR == "AK", ]
hi <- us50[us50$STATE_ABBR == "HI", ]
centerState <- function(.df) {.df$x <- .df$x - (diff(range(.df$x, na.rm = T))/2 + min(.df$x, na.rm = T))
                                .df$y <- .df$y - (diff(range(.df$y, na.rm = T))/2 + min(.df$y, na.rm = T))
                                return(.df) }
scaleState <- function(.df, scale_matrix, scale_factor, x_shift, y_shift) { .df <- centerState(.df)
                                                                            coords <- t(cbind(.df$x, .df$y)) 
                                                                            scaled_coord <- t(scale_factor*scale_matrix %*% coords) 
                                                                            .df$x <- scaled_coord[,1] + x_shift 
                                                                            .df$y <- scaled_coord[,2] + y_shift 
                                                                            return(.df) }
scale_mat <- matrix(c(1,0,0,1.25), ncol = 2, byrow = T) 
ak_scale <- scaleState(ak, scale_mat, 0.4, x_shift = -120, y_shift = 25) 
hi_scale <- scaleState(hi, scale_mat, 1.5, x_shift = -107, y_shift = 25) 
all_us <- rbind(cont_us, ak_scale, hi_scale)
#created order column to be used sorted merged dataset
all_us$order = 1:nrow(all_us)
proj_type <- "azequalarea" 
projected <- mapproject(x = all_us$x, y = all_us$y, projection=proj_type) 
all_us$x_proj <- projected[["x"]] 
all_us$y_proj <- projected[["y"]] 


# Unemployment heat map
ur_data = read.csv("allStatesMonthly.csv")
stateCodes= unique(ur_data$State)
allYears = unique(ur_data$Date)
allYearsDate = as.Date(allYears)

#GDP Data
stateDf <- read.csv('allStatesAnnually.csv', header=TRUE)
USGDPDf <- read.csv('USGDP.csv', header=TRUE)
USGDPSub <- subset(USGDPDf, Year >= 1976, select = US_GDP)
USGDPSub <- data.matrix(USGDPSub)
yearSub <- subset(stateDf, year >= 1976, select = year)
year <- data.matrix(yearSub)
allStateSub <- subset(stateDf, year >= 1976) 
allStateSub <- data.matrix(allStateSub)

shinyServer(function(input, output) {
  

  
  
  
  
  
  output$urplot <- renderPlot({
    asyr = paste(input$urYr, input$urMonth, "01", sep="-")
    ur_asof = ur_data[ur_data$Date== asyr,]
    asyr_date = as.Date(asyr)
    asyr_str = format(asyr_date, "%B %Y")
    usa_data <- merge(all_us, ur_asof, by.y="State", by.x = "STATE_ABBR")
    usa_sorted <- usa_data[order(usa_data["order"]),]
    usa_plot <- ggplot(data = usa_sorted, aes(x=x_proj, y=y_proj, group = DRAWSEQ, fill = UR)) + 
      geom_polygon(color = "black") +
      scale_fill_gradient(low = "yellow", high = "red") + 
      ggtitle(paste(asyr_str, "State Unemployment Rates", sep=" ")) +
      theme(axis.line=element_blank(),axis.text.x=element_blank(),
            axis.text.y=element_blank(),axis.ticks=element_blank(), 
            axis.title.x=element_blank(),axis.title.y=element_blank()
      )
    print(usa_plot)
  })
  
  datasetInput <- reactive({
    year1 = input$yrRange[1]
    year2 = input$yrRange[2]
    stateUR <- data.frame(colnames(stateDf))
    stateUR <- tail(stateUR, 50)
    stateUR$Difference <- 0
    names(stateUR)[names(stateUR)=="colnames.stateDf."] <- "State"
    for (state in stateUR$State)
      stateUR$Difference[stateUR$State==state] <- stateDf[stateDf$year==year2, state] - stateDf[stateDf$year==year1, state]
    top10 = head(stateUR[order(stateUR$Difference, decreasing = TRUE),],10) #return top 10 state
    return(top10) 
  })
  output$urRangeTable = renderTable({
    datasetInput()
  },include.rownames=FALSE)
  output$gdpplot <- renderPlot({
    # Plot US GDP over the same date range
    plot(year, USGDPSub, type="o", col="red", ylab="US GDP (Trillion $)", xlab="Year")
    title(main='US GDP 1976-2015')
  })
  output$annualur <- renderPlot({
    # Plot unemployment rate for a state
    state = stateCodes[as.numeric(input$stateIndex)]
    stateSub <- subset(stateDf, year >= 1976, select = state) 
    stateSub <- data.matrix(stateSub)
    plot(year, stateSub, type="o", col="blue", ylab="State Unemployment Rate (%)", xlab="Year")
    title(main=paste(state,"Unemployment Rate 1976-2015", sep=" "))
  })
  output$gdpur <- renderPlot({
    # Plot US GDP vs a single state unemployment rate
    state = stateCodes[as.numeric(input$stateIndex)]
    stateSub <- subset(stateDf, year >= 1976, select = state) 
    stateSub <- data.matrix(stateSub)
    plot(USGDPSub, stateSub, type="o", col="purple", ylab="State Unemployment Rate (%)", xlab="US GDP  (Trillion $)")
    title(main=paste(state,"Unemployment Rate 1976-2015", sep=" "))
  })
  output$urbytime <- renderPlot({
    allStateSub <- subset(stateDf, year >= 1976) 
    plot(year, allStateSub[,2],type="l", ylab="State Unemployment Rates (%)", xlab="Year")
    title(main="State Unemployment Rates 1976-2015")
    for ( i in seq(3,length( allStateSub ),1) )
      lines(year, allStateSub[,i],type="l",col=sample(rainbow(50)))
  })
 
})