import React from 'react';

const EntityRecognitionResults = ({ entityRecognition }) => {
  if (!entityRecognition) return null;

  return (
    <div className="card mb-3">
      <div className="card-header bg-white">
        <h5 className="mb-0">
          <i className="bi bi-diagram-3 me-2"></i>Entity Recognition
        </h5>
      </div>
      <div className="card-body">
        <div className="row">
          <div className="col-md-6">
            <h6>Recognized Entities</h6>
            <div className="d-flex flex-wrap gap-2">
              {entityRecognition.entities?.map((entity, index) => (
                <span key={index} className="badge bg-info">
                  {typeof entity === 'string' ? entity : `${entity.type}: ${entity.value}`}
                </span>
              ))}
            </div>
          </div>
          <div className="col-md-6">
            <h6>Confidence</h6>
            <div className="progress">
              <div
                className="progress-bar"
                style={{ width: `${(entityRecognition.confidence || 0) * 100}%` }}
              >
                {(entityRecognition.confidence || 0) * 100}%
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EntityRecognitionResults; 