import {

  BrainCircuit,
  Radar,
  ShieldCheck,
  TriangleAlert

} from "lucide-react";


export default function Dashboard() {

  const user =
    JSON.parse(

      localStorage.getItem(
        "mastercard_user"
      ) || "{}"

    );


  return (

    <div>


      <div className="page-header">


        <div>

          <span className="page-label">

            COMMAND CENTER

          </span>


          <h1>

            Welcome,
            {" "}
            {
              user.name ||
              "Analyst"
            }

          </h1>


          <p>

            Monitor the closed-loop
            AI payment fraud defense.

          </p>


        </div>


      </div>


      <div className="metric-grid">


        <Metric

          icon={<ShieldCheck />}

          title="Detection Rate"

          value="97.48%"

          text="Round 3"

        />


        <Metric

          icon={<Radar />}

          title="Generated Attacks"

          value="5000"

          text="Round 3"

        />


        <Metric

          icon={<TriangleAlert />}

          title="Missed"

          value="126"

          text="Down from 4418"

        />


        <Metric

          icon={<BrainCircuit />}

          title="Attack Families"

          value="4"

          text="Red Team"

        />


      </div>


      <div className="dashboard-panel">


        <h2>

          Closed Loop Architecture

        </h2>


        <div className="pipeline">


          <PipelineBox
            title="RED TEAM"
            text="Generate attacks"
          />


          <span>
            →
          </span>


          <PipelineBox
            title="BLUE TEAM"
            text="Detect fraud"
          />


          <span>
            →
          </span>


          <PipelineBox
            title="WEAKNESS"
            text="Store missed attacks"
          />


          <span>
            →
          </span>


          <PipelineBox
            title="RETRAIN"
            text="Offline adversarial retraining"
          />


        </div>


      </div>


    </div>

  );

}


function Metric({
  icon,
  title,
  value,
  text
}) {

  return (

    <div className="metric-card">

      <div className="metric-icon">

        {icon}

      </div>

      <span>
        {title}
      </span>

      <strong>
        {value}
      </strong>

      <small>
        {text}
      </small>

    </div>

  );

}


function PipelineBox({
  title,
  text
}) {

  return (

    <div className="pipeline-box">

      <strong>
        {title}
      </strong>

      <span>
        {text}
      </span>

    </div>

  );

}