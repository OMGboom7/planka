/*!
 * Copyright (c) 2024 PLANKA Software GmbH
 * Licensed under the Fair Use License: https://github.com/plankanban/planka/blob/master/LICENSE.md
 */

const fs = require('fs');
const { execFile } = require('child_process');
const path = require('path');
const util = require('util');

const PYTHON_PATH =
  process.platform === 'win32'
    ? path.join(sails.config.appPath, '.venv', 'Scripts', 'python.exe')
    : path.join(sails.config.appPath, '.venv', 'bin', 'python');

const promisifyExecFile = util.promisify(execFile);

module.exports = {
  inputs: {
    services: {
      type: 'json',
      required: true,
    },
    title: {
      type: 'string',
      required: true,
    },
    bodyByFormat: {
      type: 'json',
      required: true,
    },
  },

  async fn(inputs) {
    try {
      const env = {
        PATH: process.env.PATH,
        HOME: process.env.HOME,
        HTTP_PROXY: sails.config.custom.outgoingProxy,
        HTTPS_PROXY: sails.config.custom.outgoingProxy,
      };

      if (process.env.REQUESTS_CA_BUNDLE) {
        if (fs.existsSync(process.env.REQUESTS_CA_BUNDLE)) {
          env.REQUESTS_CA_BUNDLE = process.env.REQUESTS_CA_BUNDLE;
        } else {
          sails.log.warn(
            `REQUESTS_CA_BUNDLE points to missing file: ${process.env.REQUESTS_CA_BUNDLE}`,
          );
        }
      }

      await promisifyExecFile(
        PYTHON_PATH,
        [
          path.join(sails.config.appPath, 'utils', 'send_notifications.py'),
          JSON.stringify(inputs.services),
          inputs.title,
          JSON.stringify(inputs.bodyByFormat),
        ],
        {
          env,
        },
      );
    } catch (error) {
      sails.log.error(`Error sending notifications:\n${error.stderr || error.message}`);
    }
  },
};
