export const PLOTS = ['cluster_scatter', 'radar_chart', 'speed_trace', 'throttle_brake', 'sector_comparison']

export const PLOT_INFO = {
  cluster_scatter: {
    title: 'Driver Clustering',
    description: "A 2D projection (PCA) of each driver's feature profile, colored by assigned style. Drivers plotted closer together drove more similarly on the metrics measured here.",
  },
  radar_chart: {
    title: 'Style Profile',
    description: "Speed, throttle, braking, aggression, and gear usage per driver, scaled 0–1 against the others in this analysis — the shape of each line shows their overall approach at a glance.",
  },
  speed_trace: {
    title: 'Speed Trace',
    description: "Each driver's speed across their fastest lap, plotted against distance around the track — shows where one driver carried more speed through a corner or down a straight.",
  },
  throttle_brake: {
    title: 'Throttle & Brake',
    description: "Throttle percentage and brake application across the fastest lap for each driver — shows how hard, and how late, they get on and off the pedals.",
  },
  sector_comparison: {
    title: 'Sector Times',
    description: "Each driver's fastest lap split into its three sectors — highlights exactly where time was gained or lost across the lap.",
  },
}
