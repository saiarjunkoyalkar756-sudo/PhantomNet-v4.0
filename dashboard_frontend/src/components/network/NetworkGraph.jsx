import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

// This component requires the 'd3' library.
// Install it using: npm install d3

const NetworkGraph = () => {
  const d3Container = useRef(null);
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);

  useEffect(() => {
    fetch('/api/v1/network/topology')
      .then(response => response.json())
      .then(data => {
        setNodes(data.nodes);
        setLinks(data.links);
      });
  }, []);

  useEffect(() => {
    if (nodes.length > 0 && d3Container.current) {
      const svg = d3.select(d3Container.current);
      const width = 500;
      const height = 400;

      svg.attr('width', width).attr('height', height);

      const simulation = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id(d => d.id))
        .force('charge', d3.forceManyBody())
        .force('center', d3.forceCenter(width / 2, height / 2));

      const link = svg.append('g')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .selectAll('line')
        .data(links)
        .join('line')
        .attr('stroke-width', d => Math.sqrt(d.value));

      const node = svg.append('g')
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .selectAll('circle')
        .data(nodes)
        .join('circle')
        .attr('r', 10)
        .attr('fill', '#69b3a2');

      node.append('title')
        .text(d => d.id);
        
      simulation.on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        node
          .attr('cx', d => d.x)
          .attr('cy', d => d.y);
      });
    }
  }, [nodes, links]);

  return (
    <svg
      className="w-full h-full"
      ref={d3Container}
    />
  );
};

export default NetworkGraph;
