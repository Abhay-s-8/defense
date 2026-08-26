import {

  useEffect,
  useState

} from "react";


import {

  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis

} from "recharts";


import {

  api

} from "../api";


export default function Metrics() {

  const [
    metrics,
    setMetrics
  ] = useState(null);


  useEffect(

    () => {


      api
        .get("/metrics")
        .then(
          response => {

            setMetrics(
              response.data
            );

          }
        );


    },

    []

  );


  const chartData =
    metrics
    ? [

        {

          round:
            "Round 2",

          detection:
            metrics
              .round_2
              .detection_rate

        },

        {

          round:
            "Round 3",

          detection:
            metrics
              .round_3
              .detection_rate

        }

      ]
    : [];


  return (

    <div>


      <div className="page-header">


        <div>

          <span className="page-label">

            AI VS AI

          </span>


          <h1>

            Closed Loop
            Performance

          </h1>


          <p>

            Compare the model
            before and after
            adversarial retraining.

          </p>


        </div>


      </div>


      <div className="metric-grid two-metrics">


        <div className="metric-card">


          <span>

            Round 2

          </span>


          <strong>

            {
              metrics
                ?.round_2
                ?.detection_rate
              ??
              "-"
            }
            %

          </strong>


          <small>

            {
              metrics
                ?.round_2
                ?.missed
              ??
              "-"
            }
            {" "}
            missed

          </small>


        </div>


        <div className="metric-card">


          <span>

            Round 3

          </span>


          <strong>

            {
              metrics
                ?.round_3
                ?.detection_rate
              ??
              "-"
            }
            %

          </strong>


          <small>

            {
              metrics
                ?.round_3
                ?.missed
              ??
              "-"
            }
            {" "}
            missed

          </small>


        </div>


      </div>


      <div className="chart-container">


        <ResponsiveContainer
          width="100%"
          height={350}
        >


          <LineChart
            data={chartData}
          >


            <CartesianGrid

              strokeDasharray="3 3"

              stroke="#29364b"

            />


            <XAxis

              dataKey="round"

              stroke="#9aa8bd"

            />


            <YAxis

              domain={[0, 100]}

              stroke="#9aa8bd"

            />


            <Tooltip />


            <Line

              type="monotone"

              dataKey="detection"

              stroke="#61e7c8"

              strokeWidth={4}

              dot={{
                r: 7
              }}

            />


          </LineChart>


        </ResponsiveContainer>


      </div>


    </div>

  );

}