/** Composition root — wire application to infrastructure gateways. */

export {
  httpGraphGateway as graphGateway,
  httpJobFeaturesGateway as jobFeaturesGateway,
  httpJobGateway as jobGateway,
} from '@/infrastructure/gateways/httpJobGateway'
