"""
eBird API adapter stub.

This is a placeholder for future eBird API integration.
The eBird API requires registration and an API key.
"""

from typing import Any, Dict, List

import pandas as pd

from biosound.adapters.base import DataAdapter


class EBirdAPIAdapter(DataAdapter):
    """
    Adapter for fetching bird observations from the eBird API.
    
    eBird API documentation: https://documenter.getpostman.com/view/664302/S1ENwy59
    
    TODO:
    - Implement API authentication
    - Handle rate limiting
    - Map eBird taxonomy to canonical schema
    - Support geographic filtering by park boundaries
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = self.data_config.get("ebird_api_key")
    
    def list_parks(self) -> List[Dict[str, str]]:
        """
        List parks available via eBird.
        
        TODO: Implement using eBird hotspot/region endpoints.
        """
        raise NotImplementedError(
            "eBird API adapter not yet implemented.\n"
            "TODO: Implement park listing via eBird region/hotspot API.\n"
            "See https://documenter.getpostman.com/view/664302/S1ENwy59"
        )
    
    def fetch_observations(
        self,
        park_id: str,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        """
        Fetch observations from eBird API.
        
        TODO:
        - Use historic observations endpoint
        - Handle pagination
        - Map to canonical schema
        
        Args:
            park_id: Park identifier or eBird region code
            start_year: Start year
            end_year: End year
            
        Returns:
            DataFrame with canonical schema
        """
        raise NotImplementedError(
            "eBird API adapter not yet implemented.\n"
            "TODO: Implement observation fetching from eBird API.\n"
            "Will require:\n"
            "  1. API key configuration\n"
            "  2. Region/hotspot mapping to park_id\n"
            "  3. Pagination for large date ranges\n"
            "  4. Taxonomy mapping to canonical species_id\n"
            "See https://documenter.getpostman.com/view/664302/S1ENwy59"
        )
